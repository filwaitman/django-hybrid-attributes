import inspect

from .core import HybridExpression


def assert_hybrid_attributes_are_consistent(hybrid_attribute, *f_args, **f_kwargs):
    """Assert that instance- and class-level attributes are consistents with each other.

    Use it as a standalone helper (in a sanity script of some sort, for example).
    In order to use it inside a `unittest.TestCase`, consider using `HybridTestCaseMixin.assertHybridAttributesAreConsistent`.

    :param hybrid_attribute: class-level attribute to test against its relative instance-level attribute.
    :param queryset: [optional] queryset to test against. If omitted, Klass.objects.all() will be used.
    :param f_args: [optional] positional arguments that will be passed to both instance- and class-level attributes.
    :param f_kwargs: [optional] keyword arguments that will be passed to both instance- and class-level attributes.

    :Example:
    >>> assert_hybrid_attributes_are_consistent(Student.my_property)
    >>> assert_hybrid_attributes_are_consistent(Student.my_method, arg1, arg2=2)

    :raises AssertionError: when instance- and class-level attributes mismatch.

    """
    queryset = f_kwargs.pop('queryset', None)
    testcase_instance = f_kwargs.pop('_testcase_instance', None)

    hybrid_expression = hybrid_attribute
    if not isinstance(hybrid_expression, HybridExpression):
        hybrid_expression = hybrid_expression(*f_args, **f_kwargs)

    if queryset is None:
        queryset = hybrid_expression.callable.__self__.objects.all()

    for obj in queryset.annotate(hybrid_expression_result=hybrid_expression.e()):
        expression_result = obj.hybrid_expression_result

        function_result = getattr(obj, hybrid_expression.callable.__name__)
        if inspect.ismethod(function_result):
            function_result = function_result(*f_args, **f_kwargs)

        msg = f'Hybrid expression/function mismatch for id={obj.id}. Expr="{expression_result}" x Func="{function_result}"'
        if testcase_instance:
            testcase_instance.assertEqual(expression_result, function_result, msg)
        else:
            assert expression_result == function_result, msg


class HybridTestCaseMixin(object):
    def assertHybridAttributesAreConsistent(self, *args, **kwargs):
        """Unittest helper method that wraps `assert_hybrid_attributes_are_consistent()` capabilities.

        Signature is a mirror of `assert_hybrid_attributes_are_consistent()`.

        :Example:
        >>> import unittest
        >>> class MyTest(HybridTestCaseMixin, unittest.TestCase):
        ...     def test_hybrid_attributes_consistent(self):
        ...         # <Create you Klass() instances>
        ...         self.assertHybridAttributesAreConsistent(Klass.my_property)
        ...         self.assertHybridAttributesAreConsistent(Klass.my_method, arg1, arg2=2)

        """
        kwargs['_testcase_instance'] = self
        assert_hybrid_attributes_are_consistent(*args, **kwargs)
