import functools
import random
import string

from django.db import models

QS_METHOD_FILTER = 'filter'
QS_METHOD_EXCLUDE = 'exclude'


def _make_expression_result(lookup):
    def inner(hybrid_expression_instance, value):
        if hybrid_expression_instance.force_lookup:
            final_lookup = hybrid_expression_instance.force_lookup
        else:
            final_lookup = f'i{lookup}' if hybrid_expression_instance.ignore_case_in_lookup else lookup

        return HybridExpressionResult(
            expr=hybrid_expression_instance.expression(),
            value=value,
            lookup=final_lookup,
            queryset_method=hybrid_expression_instance.queryset_method,
            alias=hybrid_expression_instance.alias,
        )
    return inner


class HybridExpressionResult(object):
    def __init__(self, expr, value, lookup, queryset_method, alias=None):
        self.expr = expr
        self.value = value
        self.lookup = lookup
        self.queryset_method = queryset_method
        self.alias = alias or self._generate_alias()

    def _generate_alias(self):
        return 'hybrid_' + ''.join(random.choice(string.ascii_lowercase) for _ in range(10))

    def _apply_filter(self, queryset):
        qs = queryset.annotate(**{self.alias: self.expr})

        value = self.value
        if isinstance(value, HybridExpression):
            alias2 = value.alias or self._generate_alias()
            qs = qs.annotate(**{alias2: value.expression()})
            value = models.F(f'{alias2}')

        return getattr(qs, self.queryset_method)(**{f'{self.alias}__{self.lookup}': value})


class HybridExpression(object):
    def __init__(self, callable_, callable_args=(), callable_kwargs={}, ignore_case_in_lookup=False, queryset_method=QS_METHOD_FILTER, force_lookup='', alias=None):  # noqa
        self.callable = callable_
        self.callable_args = callable_args
        self.callable_kwargs = callable_kwargs
        self.ignore_case_in_lookup = ignore_case_in_lookup
        self.queryset_method = queryset_method
        self.force_lookup = force_lookup
        self.alias = alias

    __lt__ = _make_expression_result('lt')
    __le__ = _make_expression_result('lte')
    __gt__ = _make_expression_result('gt')
    __ge__ = _make_expression_result('gte')
    __eq__ = _make_expression_result('exact')
    is_ = __eq__

    def __ne__(self, value):
        return self.__invert__().__eq__(value)

    def __invert__(self):
        queryset_method = (
            QS_METHOD_EXCLUDE
            if (self.queryset_method == QS_METHOD_FILTER)
            else QS_METHOD_FILTER
        )
        return self._clone(queryset_method=queryset_method)

    def _clone(self, **overrides):
        instance = self.__class__(
            callable_=overrides.get('callable_', self.callable),
            callable_args=overrides.get('callable_args', self.callable_args),
            callable_kwargs=overrides.get('callable_kwargs', self.callable_kwargs),
            ignore_case_in_lookup=overrides.get('ignore_case_in_lookup', self.ignore_case_in_lookup),
            queryset_method=overrides.get('queryset_method', self.queryset_method),
            force_lookup=overrides.get('force_lookup', self.force_lookup),
            alias=overrides.get('alias', self.alias),
        )
        return instance

    def alias(self, alias):
        """Force a particular alias to be used when annotating this expression to queryset.

        Usually alias is generated automatically and randomly in order to avoid name collisions.
        Using a non-random alias is handy when one intends to use this annotation later on (in an order_by, for instance).

        :param alias: alias to be used.
        :type alias: str

        :Example:
        >>> Klass.objects.filter(Klass.my_property.a('_prop') == 'whatever').order_by('_prop')

        """
        return self._clone(alias=alias)
    a = alias

    def expression(self):
        """Get the raw expression (meaning: the pure result of hybrid_property/hybrid_expression call).

        The returned raw expression can be used however one wants (for instance, inside a `.annotate()` call).

        :Example:
        >>> Klass.objects.annotate(_prop=Klass.my_property.e())

        """
        return self.callable(*self.callable_args, **self.callable_kwargs)
    e = expression

    def ignore_case(self):
        """Mark the expression to use ignore_case version of lookup.

        In practice appends the 'i' in lookup.

        :Example:
        >>> Klass.objects.filter(Klass.my_property == 'whatever')  # lookup used: exact
        >>> Klass.objects.filter(Klass.my_property.i() == 'whatever')  # lookup used: iexact

        """
        return self._clone(ignore_case_in_lookup=True)
    i = ignore_case

    def lookup(self, lookup):
        """Force a particular lookup to be used in this expression.

        :param lookup: lookup to be used.
        :type lookup: str

        :Example:
        >>> Klass.objects.filter(Klass.my_property.l('startswith') == 'whatever')

        """
        return self._clone(force_lookup=lookup)
    l = lookup  # noqa

    def through(self, through):
        """Make a relation (join) between current class and a target path.

        :param through: path to relate to. Do not end the parameter with `__` as this will be done automatically.
        :type through: str

        :Example:
        >>> Klass.objects.filter(Child.my_property.t('parent') == 'whatever')
        >>> Klass.objects.filter(GrandChild.my_property.t('child__parent') == 'whatever')

        """
        assert not through.endswith('__'), 'No need to add explictly `__` to the end of through relation'
        return self._clone(callable_=functools.partial(self.callable, through=f'{through}__'))
    t = through
