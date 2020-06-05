[![Travis](https://travis-ci.com/filwaitman/django-hybrid-attributes.svg?branch=master)](https://travis-ci.com/filwaitman/django-hybrid-attributes)
[![Codecov](https://codecov.io/gh/filwaitman/django-hybrid-attributes/branch/master/graph/badge.svg)](https://codecov.io/gh/filwaitman/django-hybrid-attributes)
[![PyPI](https://img.shields.io/pypi/v/django-hybrid-attributes.svg)](https://pypi.python.org/pypi/django-hybrid-attributes/)
[![License](https://img.shields.io/pypi/l/django-hybrid-attributes.svg)](https://pypi.python.org/pypi/django-hybrid-attributes/)
[![Python versions](https://img.shields.io/pypi/pyversions/django-hybrid-attributes.svg)](https://pypi.python.org/pypi/django-hybrid-attributes/)
[![PyPI downloads per month](https://img.shields.io/pypi/dm/django-hybrid-attributes.svg)](https://pypi.python.org/pypi/django-hybrid-attributes/)


# Django Hybrid Attributes

This is a (pretty basic) implementation of the [SQLAlchemy Hybrid Attributes](https://docs.sqlalchemy.org/en/13/orm/extensions/hybrid.html) for Django - more precisely `hybrid_property` and `hybrid_method`.


## Example of basic usage:
```python
from django.db import models
from django_hybrid_attributes import hybrid_method, hybrid_property, HybridQuerySet


class User(models.Model):
    first_name = models.CharField(max_length=63)
    last_name = models.CharField(max_length=63)
    some_value = models.PositiveSmallIntegerField()
    objects = HybridQuerySet.as_manager()

    @hybrid_property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @full_name.expression
    def full_name(cls, through=''):
        return models.functions.Concat(f'{through}first_name', models.Value(' '), f'{through}last_name')

    @hybrid_method
    def some_value_plus_n(self, n):
        return self.some_value + n

    @some_value_plus_n.expression
    def some_value_plus_n(cls, n, through=''):
        return models.F(f'{through}some_value') + models.Value(n)


user1 = User.objects.create(first_name='Filipe', last_name='Waitman', some_value=10)
user2 = User.objects.create(first_name='Agent', last_name='Smith', some_value=5)

# Compatible with regular django .filter() - so this won't break your existing code
assert User.objects.filter(first_name='Filipe').count() == 1
assert User.objects.filter(models.Q(last_name='Waitman')).count() == 1

# hybrid_property/hybrid_method functions are common properties/methods
assert user1.full_name == 'Filipe Waitman'
assert user2.some_value_plus_n(10) == 15

# hybrid_property/hybrid_method expressions are translated to Q() objects, annotated, and filtered accordingly
assert User.objects.filter(User.full_name == 'Filipe Waitman').count() == 1
assert User.objects.filter(User.full_name == 'FILIPE WAITMAN').count() == 0
assert User.objects.filter(User.full_name != 'FILIPE WAITMAN').count() == 2
assert User.objects.filter(User.full_name.i() == 'FILIPE WAITMAN').count() == 1  # .i() ignores case, so iexact is applied
assert User.objects.filter(User.full_name.i().l('contains') == 'WAIT').count() == 1  # icontains is applied
assert User.objects.filter(User.some_value_plus_n(20) < 25).count() == 0
assert User.objects.filter(User.some_value_plus_n(20) > 25).count() == 1
assert User.objects.filter(User.some_value_plus_n(20) >= 25).count() == 2

# `.e()` returns the equivalent Django expression so you can use it as you wish
qs = User.objects.annotate(value_plus_3=User.some_value_plus_n(3).e())
assert [x.value_plus_3 for x in qs.order_by('value_plus_3')] == [8, 13]
```

For another examples, please refer to the tests folder.

## Features:
- Filter support using Python magic methods. Examples:
```python
Klass.objects.filter(Klass.my_hybrid_property == 'value')  # lookup=exact
Klass.objects.filter(Klass.my_hybrid_property.i() == 'value')  # lookup=iexact
Klass.objects.filter(Klass.my_hybrid_property != 'value')  # lookup=exact, queryset_method=exclude
Klass.objects.filter(~Klass.my_hybrid_property == 'value')  # lookup=exact, queryset_method=exclude
Klass.objects.filter(Klass.my_hybrid_property > 'value')  # lookup=gt
Klass.objects.filter(Klass.my_hybrid_property < 'value')  # lookup=lt
Klass.objects.filter(Klass.my_hybrid_property >= 'value')  # lookup=gte
Klass.objects.filter(Klass.my_hybrid_property <= 'value')  # lookup=lte
```

- Support of all django lookups via `l()` attribute. Examples:
```python
Klass.objects.filter(Klass.my_hybrid_property.l('istartswith') == 'value')
Klass.objects.filter(Klass.my_hybrid_property.i().l('startswith') == 'value')  # lookup=istartswith
Klass.objects.filter(Klass.my_hybrid_property.l('contains') == 'value')
Klass.objects.filter(Klass.my_hybrid_property.l('date__year') == 'value')
```

- Relations support via `t()` attribute. Examples:
```python
Klass.objects.filter(Parent.my_hybrid_property.t('parent') == 'value')
Klass.objects.filter(GrandParent.my_hybrid_property.t('parent__grandparent') > 'value')
Klass.objects.filter(Child.my_hybrid_property.t('children') < 'value')
```

- Raw expressions (for you to use it whatever you want) via `.e()` attribute. Examples:
```python
Klass.objects.annotate(my_method_result=Klass.my_hybrid_method().e())
```

- Custom alias via `.a()` attribute (so you can reference the annotated expression later on). Examples:
```python
Klass.objects.filter(Klass.my_hybrid_property.a('_expr_alias') > 'value').order_by('_expr_alias')
```

- Test/script helper to ensure hybrid expressions are sane compared to its properties/methods. Examples:
```python
from django_hybrid_attributes.test_utils import assert_hybrid_attributes_are_consistent, HybridTestCaseMixin


class MyTestCase(HybridTestCaseMixin, YourBaseTestcase):
    def test_expressions_are_sane(self):
        self.assertHybridAttributesAreConsistent(Klass.my_hybrid_property)
        self.assertHybridAttributesAreConsistent(Klass.my_hybrid_method_without_args)

        # In order to pass arguments to your function, pass them as args/kwargs in the assert call:
        self.assertHybridAttributesAreConsistent(Klass.my_hybrid_method_with_args, 1)
        self.assertHybridAttributesAreConsistent(Klass.my_hybrid_method_with_args, n=1)

        # By default this will compare return of expression/function for all instances (Klass.objects.all()).
        # In order to run for a subset of results use the `queryset` param:
        self.assertHybridAttributesAreConsistent(Klass.my_hybrid_property, queryset=Klass.objects.filter(id=1))

        # You can also use it as a helper (outside of tests scope) of some sort (HybridTestCaseMixin is not required):
        assert_hybrid_attributes_are_consistent(Klass.my_hybrid_property)
```

- No dark magic: under the hood, all it does is to `annotate()` an expression to a queryset and `filter/exclude()` using this annotation.


## FAQ

### Q: Why do I need this project? Couldn't I use `Klass.objects.annotate(whatever=<expression>).filter(whatever=<value>)`?
A: You don't need this project. And you could use this approach.
That being said, I still see some reasons to use this project, such as:
- Cleaner and more concise code;
- Support for relations via `.t()/.through()`;
- Better code placement (method and its expression lives alongside each other, instead of spread over 2 different files (models.py and managers.py))

### Q: Why is this `.t()` needed? Couldn't I use `through` parameter directly?
A: You could do that for hybrid_methods (and you can, nothing stops you from doing this). However, this wouldn't work for hybrid_properties for obvious reasons. =P

### Q: SQLAlchemy creates automatically the `.expression` function for the simplest cases. Does this project do it as well?
A: No, I didn't find a decent (meaning: non-smelly) way of doing this using Django structure (yet). Suggestions are welcome.

### Q: Why is there that amount of abbreviations in the code?
A: I don't like code abbreviations either. However, Django querysets are rather way too long which makes them hard to read anyway. This is an attempt to make them a bit shorter.
Still, if you don't buy it, you can use the non-abbreviated aliases:
- `.a()` --> `.alias()`
- `.e()` --> `.expression()`
- `.i()` --> `.ignore_case_in_lookup()`
- `.l()` --> `.lookup()`
- `.t()` --> `.through()`


## Limitations and known issues

* `.expression()` must return a plain Django expression (at least for now).
It means that if, for instance, an expression depends on a prior annotation, at least the prior annotation must be done out of the `.expression()` attribute (which might be a bad design as the logic would be kind of segmented).

* There's no interface to call `.distinct()` for the expressions. So `Klass.my_property.t('this__duplicates__rows')` might return duplicated rows (specially on reverse relationships via `.t()`)


## Development:

### Run linter:
```bash
pip install -r requirements_dev.txt
isort -rc .
tox -e lint
```

### Run tests via `tox`:
```bash
pip install -r requirements_dev.txt
tox
```

### Release a new major/minor/patch version:
```bash
pip install -r requirements_dev.txt
bump2version <PART>  # <PART> can be either 'patch' or 'minor' or 'major'
```

### Upload to PyPI:
```bash
pip install -r requirements_dev.txt
python setup.py sdist bdist_wheel
python -m twine upload dist/*
```


## Contributing:

Please [open issues](https://github.com/filwaitman/django-hybrid-attributes/issues) if you see one, or [create a pull request](https://github.com/filwaitman/django-hybrid-attributes/pulls) when possible.
In case of a pull request, please consider the following:
- Respect the line length (132 characters)
- Write automated tests
- Run `tox` locally so you can see if everything is green (including linter and other python versions)
