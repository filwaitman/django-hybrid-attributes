import functools

from .core import HybridExpression


class hybrid_method(object):
    """Decorator which allows definition of a Python method with both instance- and class-level behavior.

    Just like SQLAlchemy, class-level behavior is achieved by using `.expression()`.

    :Example:

    >>> from django.db import models
    >>> from django_hybrid_attributes import HybridQuerySet, hybrid_method
    >>> class User(models.Model):
    ...     some_value = models.PositiveSmallIntegerField()
    ...     objects = HybridQuerySet.as_manager()
    ...
    ...     @hybrid_method
    ...     def some_value_plus_n(self, n):
    ...         return self.some_value + n
    ...
    ...     @some_value_plus_n.expression
    ...     def some_value_plus_n(cls, n, through=''):
    ...         return models.F(f'{through}some_value') + models.Value(n)

    """

    def __init__(self, func):
        self.func = func
        self.expr = None

    def __get__(self, instance, owner):
        if instance is None:
            return self._hybrid_expression_wrapper(self.expr.__get__(owner, owner.__class__))
        else:
            return self.func.__get__(instance, owner)

    def _hybrid_expression_wrapper(self, expr):
        @functools.wraps(expr)
        def inner(*args, **kwargs):
            return HybridExpression(expr, callable_args=args, callable_kwargs=kwargs)
        return inner

    def expression(self, expr):
        """Decorator which defines the Django expression to be used for this hybrid attribute.

        Unlike SQLAlchemy, the `.expression()` decorated method MUST be provided - this package won't try to guess the expression.

        """
        self.expr = expr
        return self


class hybrid_property(hybrid_method):
    """Decorator which allows definition of a Python descriptor with both instance- and class-level behavior.

    Instance-level property is still a property so setters/deleters will work normally.
    Just like SQLAlchemy, class-level behavior is achieved by using `.expression()`.

    :Example:

    >>> from django.db import models
    >>> from django_hybrid_attributes import HybridQuerySet, hybrid_property
    >>> class User(models.Model):
    ...     first_name = models.CharField(max_length=63)
    ...     last_name = models.CharField(max_length=63)
    ...     objects = HybridQuerySet.as_manager()
    ...
    ...     @hybrid_property
    ...     def full_name(self):
    ...         return f'{self.first_name} {self.last_name}'
    ...
    ...     @full_name.expression
    ...     def full_name(cls, through=''):
    ...         return models.functions.Concat(f'{through}first_name', models.Value(' '), f'{through}last_name')

    """

    def __init__(self, func):
        super().__init__(func)
        self.func_setter = None
        self.func_deleter = None

    def __get__(self, instance, owner):
        return super().__get__(instance, owner)()  # Note the trailing parenthesis, we're calling the *result* of super()

    def __set__(self, instance, value):
        if self.func_setter is None:
            raise AttributeError("can't set attribute")
        self.func_setter(instance, value)

    def __delete__(self, instance):
        if self.func_deleter is None:
            raise AttributeError("can't delete attribute")
        self.func_deleter(instance)

    def setter(self, func_setter):
        self.func_setter = func_setter
        return self

    def deleter(self, func_deleter):
        self.func_deleter = func_deleter
        return self
