from django.db import models
from django.test import TestCase

from django_hybrid_attributes.test_utils import HybridTestCaseMixin, assert_hybrid_attributes_are_consistent

from .models import Classroom, Student, StudentClassroom, Teacher


class HighLevelTestCase(HybridTestCaseMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.teacher1 = Teacher.objects.create(first_name='Teacher', last_name='First')
        self.teacher2 = Teacher.objects.create(first_name='Teacher', last_name='Second')
        self.classroom1 = Classroom.objects.create(name='Boring stuff', teacher=self.teacher1)
        self.classroom2 = Classroom.objects.create(name='IT and software development', teacher=self.teacher2)
        self.student1 = Student.objects.create(magic_number1=1, magic_number2=2, first_name='Filipe', last_name='Waitman')
        self.student2 = Student.objects.create(magic_number1=3, magic_number2=4, first_name='Agent', last_name='Smith')
        self.student1_classroom1 = StudentClassroom.objects.create(student=self.student1, classroom=self.classroom1, grade=5)
        self.student1_classroom2 = StudentClassroom.objects.create(student=self.student1, classroom=self.classroom2, grade=7)
        self.student2_classroom1 = StudentClassroom.objects.create(student=self.student2, classroom=self.classroom1, grade=9)

    def test_hybrid_attributes_are_consistent(self):
        self.assertHybridAttributesAreConsistent(Student.magic_number_sum)
        self.assertHybridAttributesAreConsistent(Student.magic_number1_times_n, n=3)
        self.assertHybridAttributesAreConsistent(Student.full_name)
        self.assertHybridAttributesAreConsistent(Student.full_name_lowercased)
        self.assertHybridAttributesAreConsistent(Student.get_status)
        self.assertHybridAttributesAreConsistent(Teacher.full_name)
        self.assertHybridAttributesAreConsistent(Classroom.is_about_technology)
        self.assertHybridAttributesAreConsistent(StudentClassroom.passed)
        self.assertHybridAttributesAreConsistent(StudentClassroom.get_grade_as_percent)

        # `self.assertHybridAttributesAreConsistent` and `assert_hybrid_attributes_are_consistent` are pretty much the same thing.
        # I'm keeping both versions here for demonstration purposes.
        assert_hybrid_attributes_are_consistent(Student.magic_number_sum)
        assert_hybrid_attributes_are_consistent(Student.magic_number1_times_n, n=3)
        assert_hybrid_attributes_are_consistent(Student.full_name)
        assert_hybrid_attributes_are_consistent(Student.full_name_lowercased)
        assert_hybrid_attributes_are_consistent(Student.get_status)
        assert_hybrid_attributes_are_consistent(Teacher.full_name)
        assert_hybrid_attributes_are_consistent(Classroom.is_about_technology)
        assert_hybrid_attributes_are_consistent(StudentClassroom.passed)
        assert_hybrid_attributes_are_consistent(StudentClassroom.get_grade_as_percent)

    def test_hybrid_property_function(self):
        # Watch out, self.assertEqual won't work directly
        self.assertEqual(self.student1.full_name == 'Filipe Waitman', True)
        self.assertEqual(self.student2.full_name == 'Filipe Waitman', False)

    def test_hybrid_method_function(self):
        # Watch out, self.assertEqual won't work directly
        self.assertEqual(self.student1.magic_number1_times_n(5) == 5, True)
        self.assertEqual(self.student1.magic_number1_times_n(10) > 100, False)
        self.assertEqual(self.student2.magic_number1_times_n(15) == 45, True)

    def test_hybrid_property_filter_works_with_django_filter_capabilities_altogether(self):
        qs = Student.objects.filter(
            models.Q(magic_number1__gte=1),
            Student.magic_number_sum <= 5,
            models.Q(magic_number2__gt=1),
            first_name='NOBODY HERE',
        )
        self.assertEqual(qs.count(), 0)

        qs = Student.objects.filter(
            models.Q(magic_number1__gte=3),
            Student.magic_number_sum <= 5,
            models.Q(magic_number2__gt=1),
            first_name='Filipe',
        )
        self.assertEqual(qs.count(), 0)

        qs = Student.objects.filter(
            models.Q(magic_number1__gte=1),
            Student.magic_number_sum <= 5,
            models.Q(magic_number2__gt=1),
            first_name='Filipe',
        )
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student1)

    def test_hybrid_method_filter_works_with_django_filter_capabilities_altogether(self):
        qs = Student.objects.filter(
            models.Q(magic_number1__gte=1),
            Student.magic_number1_times_n(5) < 10,
            models.Q(magic_number2__gt=1),
            first_name='NOBODY HERE',
        )
        self.assertEqual(qs.count(), 0)

        qs = Student.objects.filter(
            models.Q(magic_number1__gte=3),
            Student.magic_number1_times_n(5) < 10,
            models.Q(magic_number2__gt=1),
            first_name='Filipe',
        )
        self.assertEqual(qs.count(), 0)

        qs = Student.objects.filter(
            models.Q(magic_number1__gte=1),
            Student.magic_number1_times_n(5) < 10,
            models.Q(magic_number2__gt=1),
            first_name='Filipe',
        )
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student1)

    def test_hybrid_property_lookup_exact(self):
        qs = Student.objects.filter(Student.full_name == 'Filipe Waitman')
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student1)

    def test_hybrid_method_lookup_exact(self):
        qs = Student.objects.filter(Student.magic_number1_times_n(3) == 9)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student2)

    def test_hybrid_property_lookups_gt_and_gte(self):
        qs = Student.objects.filter(Student.magic_number_sum > 3)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student2)

        qs = Student.objects.filter(Student.magic_number_sum >= 3)
        self.assertEqual(qs.count(), 2)

    def test_hybrid_method_lookups_gt_and_gte(self):
        qs = Student.objects.filter(Student.magic_number2_times_n(2) > 4)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student2)

        qs = Student.objects.filter(Student.magic_number2_times_n(2) >= 4)
        self.assertEqual(qs.count(), 2)

    def test_hybrid_property_lookups_lt_and_lte(self):
        qs = Student.objects.filter(Student.magic_number_sum < 3)
        self.assertEqual(qs.count(), 0)

        qs = Student.objects.filter(Student.magic_number_sum <= 3)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student1)

    def test_hybrid_method_lookups_lt_and_lte(self):
        qs = Student.objects.filter(Student.magic_number2_times_n(2) < 4)
        self.assertEqual(qs.count(), 0)

        qs = Student.objects.filter(Student.magic_number2_times_n(2) <= 4)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student1)

    def test_hybrid_property_lookups_flag_ignorecase(self):
        qs = Student.objects.filter(Student.full_name == 'FILIPE WAITMAN')
        self.assertEqual(qs.count(), 0)

        qs = Student.objects.filter(Student.full_name.i() == 'FILIPE WAITMAN')
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student1)

    def test_hybrid_method_lookups_flag_ignorecase(self):
        qs = Student.objects.filter(Student.get_status() == 'FAILED')
        self.assertEqual(qs.count(), 0)

        qs = Student.objects.filter(Student.get_status().i() == 'FAILED')
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student1)

    def test_hybrid_property_exclude_unary(self):
        qs = Student.objects.filter(~Student.full_name == 'Filipe Waitman')
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student2)

    def test_hybrid_method_exclude_unary(self):
        qs = Student.objects.filter(~Student.magic_number1_times_n(3) == 9)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student1)

    def test_hybrid_property_exclude_different(self):
        qs = Student.objects.filter(Student.full_name != 'filipe waitman')
        self.assertEqual(qs.count(), 2)

        qs = Student.objects.filter(Student.full_name.i() != 'filipe waitman')
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student2)

        qs = Student.objects.filter(~Student.full_name.i() != 'filipe waitman')
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student1)

    def test_hybrid_method_exclude_different(self):
        qs = Student.objects.filter(~Student.magic_number1_times_n(3) != 9)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student2)

    def test_hybrid_property_lookup_custom(self):
        qs = Student.objects.filter(Student.full_name.l('endswith') == 'itman')
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student1)

        qs = Student.objects.filter(Student.full_name.i().l('startswith') == 'FILI')  # Final lookup will be istartswith
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student1)

    def test_hybrid_method_lookup_custom(self):
        qs = Student.objects.filter(Student.get_status().l('endswith') == 'iled')
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student1)

        qs = Student.objects.filter(Student.get_status().i().l('startswith') == 'FAIL')  # Final lookup will be istartswith
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student1)

    def test_hybrid_property_alias(self):
        qs = Student.objects.filter(Student.full_name.a('_full_name') != 'whatever').order_by('_full_name')
        self.assertEqual(qs.count(), 2)
        instance1, instance2 = qs.all()
        self.assertEqual(instance1, self.student2)
        self.assertEqual(instance1._full_name, 'Agent Smith')
        self.assertEqual(instance2, self.student1)
        self.assertEqual(instance2._full_name, 'Filipe Waitman')

    def test_hybrid_method_alias(self):
        qs = Student.objects.filter(Student.magic_number1_times_n(2).a('_doubled') >= 0).order_by('-_doubled')
        self.assertEqual(qs.count(), 2)
        instance1, instance2 = qs.all()
        self.assertEqual(instance1, self.student2)
        self.assertEqual(instance1._doubled, 6)
        self.assertEqual(instance2, self.student1)
        self.assertEqual(instance2._doubled, 2)

    def test_hybrid_property_relations(self):
        qs = Student.objects.filter(StudentClassroom.passed.t('studentclassroom').is_(False))
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student1)

        qs = Student.objects.filter(StudentClassroom.passed.t('studentclassroom').is_(True))
        self.assertEqual(qs.count(), 2)

        qs = Student.objects.filter(Classroom.is_about_technology.t('studentclassroom__classroom').is_(True))
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student1)

        qs = StudentClassroom.objects.filter(Student.full_name.i().t('student') == 'FILIPE WAITMAN')
        self.assertEqual(qs.count(), 2)
        self.assertEqual(qs.filter(id__in=(self.student1_classroom1.id, self.student1_classroom2.id)).count(), 2)

    def test_hybrid_method_relations(self):
        qs = Student.objects.filter(StudentClassroom.get_grade_as_percent().t('studentclassroom') < 0.7).distinct()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student1)

        qs = StudentClassroom.objects.filter(Student.get_status().i().t('student') == 'FAILED')
        self.assertEqual(qs.count(), 2)
        self.assertEqual(qs.filter(id__in=(self.student1_classroom1.id, self.student1_classroom2.id)).count(), 2)

    def test_hybrid_property_expressions_as_target_value(self):
        qs = Student.objects.filter(Student.full_name == Student.full_name_lowercased)
        self.assertEqual(qs.count(), 0)

        self.student1.first_name = 'filipe'
        self.student1.last_name = 'waitman'
        self.student1.save()
        qs = Student.objects.filter(Student.full_name == Student.full_name_lowercased)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student1)

    def test_hybrid_method_expressions_as_target_value(self):
        qs = Student.objects.filter(Student.magic_number1_times_n(4) == Student.magic_number2_times_n(2))
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), self.student1)

    def test_hybrid_property_instances_are_not_the_same(self):
        expression1 = Student.full_name
        expression2 = Student.full_name
        self.assertEqual(expression1.ignore_case_in_lookup, False)
        self.assertEqual(expression2.ignore_case_in_lookup, False)
        expression2 = expression2.i()
        self.assertEqual(expression1.ignore_case_in_lookup, False)
        self.assertEqual(expression2.ignore_case_in_lookup, True)

    def test_hybrid_method_instances_are_not_the_same(self):
        expression1 = Student.magic_number1_times_n(1)
        expression2 = Student.magic_number1_times_n(1)
        self.assertEqual(expression1.ignore_case_in_lookup, False)
        self.assertEqual(expression2.ignore_case_in_lookup, False)
        expression2 = expression2.i()
        self.assertEqual(expression1.ignore_case_in_lookup, False)
        self.assertEqual(expression2.ignore_case_in_lookup, True)

    def test_hybrid_property_as_django_expression(self):
        qs = Student.objects.annotate(x=Student.full_name.e())
        assert qs.filter(id=self.student1.id).get().x == self.student1.full_name
        assert qs.filter(id=self.student2.id).get().x == self.student2.full_name

    def test_hybrid_method_as_django_expression(self):
        qs = Student.objects.annotate(x=Student.magic_number1_times_n(3).e())
        assert qs.filter(id=self.student1.id).get().x == self.student1.magic_number1_times_n(3)
        assert qs.filter(id=self.student2.id).get().x == self.student2.magic_number1_times_n(3)

    def test_hybrid_property_function_is_still_a_property_descriptor(self):
        self.assertEqual(self.student1.full_name, 'Filipe Waitman')

        self.student1.full_name = 'Filipe Something Else'
        self.assertEqual(self.student1.first_name, 'Filipe')
        self.assertEqual(self.student1.last_name, 'Something Else')

        del self.student1.full_name
        self.assertEqual(self.student1.first_name, None)
        self.assertEqual(self.student1.last_name, None)

        with self.assertRaises(AttributeError) as exc:
            self.student1.full_name_lowercased = 'whatever this is readonly'
        self.assertEqual(f'{exc.exception}', "can't set attribute")

        with self.assertRaises(AttributeError) as exc:
            del self.student1.full_name_lowercased
        self.assertEqual(f'{exc.exception}', "can't delete attribute")

    def test_hybrid_method_metadata(self):
        self.assertEqual(self.student1.magic_number1_times_n.__name__, 'magic_number1_times_n')
        self.assertEqual(self.student1.magic_number1_times_n.__doc__, ' docstring for magic_number1_times_n ')

        self.assertEqual(Student.magic_number1_times_n.__name__, 'magic_number1_times_n')
        self.assertEqual(Student.magic_number1_times_n.__doc__, ' docstring for expr magic_number1_times_n ')
