from django.core.validators import MaxValueValidator
from django.db import models

from django_hybrid_attributes import HybridManager, HybridQuerySet, hybrid_method, hybrid_property


class Student(models.Model):
    magic_number1 = models.IntegerField()
    magic_number2 = models.IntegerField()
    first_name = models.CharField(max_length=63)
    last_name = models.CharField(max_length=63)

    objects = HybridQuerySet.as_manager()

    @hybrid_method
    def magic_number1_times_n(self, n):
        ''' docstring for magic_number1_times_n '''
        return self.magic_number1 * n

    @magic_number1_times_n.expression
    def magic_number1_times_n(cls, n, through=''):
        ''' docstring for expr magic_number1_times_n '''
        return models.F(f'{through}magic_number1') * n

    @hybrid_method
    def magic_number2_times_n(self, n):
        ''' docstring for magic_number2_times_n '''
        return self.magic_number2 * n

    @magic_number2_times_n.expression
    def magic_number2_times_n(cls, n, through=''):
        ''' docstring for expr magic_number2_times_n '''
        return models.F(f'{through}magic_number2') * n

    @hybrid_property
    def magic_number_sum(self):
        return self.magic_number1 + self.magic_number2

    @magic_number_sum.expression
    def magic_number_sum(cls, through=''):
        return models.F(f'{through}magic_number1') + models.F(f'{through}magic_number2')

    @hybrid_property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @full_name.setter
    def full_name(self, value):
        self.first_name, self.last_name = value.split(' ', 1)

    @full_name.deleter
    def full_name(self):
        self.first_name = self.last_name = None

    @classmethod
    def _full_name_expr(cls, through=''):
        return models.functions.Concat(f'{through}first_name', models.Value(' '), f'{through}last_name')

    @full_name.expression
    def full_name(cls, through=''):
        ''' docstring for expr full_name '''
        return cls._full_name_expr(through)

    @hybrid_property
    def full_name_lowercased(self):
        return self.full_name.lower()

    @full_name_lowercased.expression
    def full_name_lowercased(cls, through=''):
        return models.functions.Lower(cls._full_name_expr(through))

    @hybrid_method
    def get_status(self):
        if self.studentclassroom_set.filter(grade__lt=7).exists():
            return 'failed'
        else:
            return 'passed'

    @get_status.expression
    def get_status(cls, through=''):
        return models.Case(
            models.When(
                **{f'{through}id__in': Student.objects.exclude(studentclassroom__grade__lt=7).values('id')}, 
                then=models.Value('passed')
            ),
            default=models.Value('failed'),
            output_field=models.CharField()
        )

    # NOTE: 4 methods below are wrong by design, as we want to test the error scenarios in assert_hybrid_attributes_are_consistent.

    @hybrid_property
    def WRONG_full_name(self):
        return f'{self.first_name} {self.last_name}'

    @WRONG_full_name.expression
    def WRONG_full_name(cls, through=''):
        return models.functions.Concat(f'{through}first_name', models.Value(' WRONG '), f'{through}last_name')

    @hybrid_method
    def WRONG_magic_number1_times_n(self, n):
        return self.magic_number1 * n

    @WRONG_magic_number1_times_n.expression
    def WRONG_magic_number1_times_n(cls, n, through=''):
        return models.F(f'{through}magic_number1') * (n + 1)


class Teacher(models.Model):
    first_name = models.CharField(max_length=63)
    last_name = models.CharField(max_length=63)

    objects = HybridManager()

    @hybrid_property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @full_name.expression
    def full_name(cls, through=''):
        ''' docstring for expr full_name '''
        return models.functions.Concat(f'{through}first_name', models.Value(' '), f'{through}last_name')


class Classroom(models.Model):
    name = models.CharField(max_length=63)
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE)

    objects = HybridQuerySet.as_manager()

    @hybrid_property
    def is_about_technology(self):
        return 'IT' in self.name

    @is_about_technology.expression
    def is_about_technology(cls, through=''):
        return models.Case(
            models.When(**{f'{through}name__contains': 'IT', 'then': True}),
            default=False,
            output_field=models.BooleanField()
        )


class StudentClassroom(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    classroom = models.ForeignKey('Classroom', on_delete=models.CASCADE)
    grade = models.PositiveSmallIntegerField(validators=[MaxValueValidator(10)])

    objects = HybridManager()

    @hybrid_property
    def passed(self):
        return self.grade >= 7

    @passed.expression
    def passed(cls, through=''):
        return models.Case(
            models.When(**{f'{through}grade__gte': 7, 'then': True}),
            default=False,
            output_field=models.BooleanField()
        )

    @hybrid_method
    def get_grade_as_percent(self):
        return self.grade / 10

    @get_grade_as_percent.expression
    def get_grade_as_percent(cls, through=''):
        return models.ExpressionWrapper(models.F(f'{through}grade') / 10.0, output_field=models.FloatField())
