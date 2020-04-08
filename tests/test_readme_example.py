from django.db import models

from django_hybrid_attributes import HybridQuerySet, hybrid_method, hybrid_property


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


from django.test import TestCase  # noqa  # isort:skip
class Test(TestCase):  # noqa
    def test(self):
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
