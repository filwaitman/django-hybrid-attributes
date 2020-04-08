from django.test import TestCase

from django_hybrid_attributes.test_utils import HybridTestCaseMixin, assert_hybrid_attributes_are_consistent

from .models import Student


class assertHybridAttributesAreConsistentTestCase(HybridTestCaseMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.student1 = Student.objects.create(magic_number1=1, magic_number2=2, first_name='Filipe', last_name='Waitman')
        self.student2 = Student.objects.create(magic_number1=3, magic_number2=4, first_name='Agent', last_name='Smith')

    def test_success_cases(self):
        self.assertHybridAttributesAreConsistent(Student.full_name)
        self.assertHybridAttributesAreConsistent(Student.magic_number_sum)
        self.assertHybridAttributesAreConsistent(Student.get_status)
        assert_hybrid_attributes_are_consistent(Student.full_name)
        assert_hybrid_attributes_are_consistent(Student.magic_number_sum)
        assert_hybrid_attributes_are_consistent(Student.get_status)

    def test_error_cases(self):
        self.assertRaises(AssertionError, self.assertHybridAttributesAreConsistent, Student.WRONG_full_name)
        self.assertRaises(AssertionError, self.assertHybridAttributesAreConsistent, Student.WRONG_magic_number1_times_n, n=3)
        self.assertRaises(AssertionError, assert_hybrid_attributes_are_consistent, Student.WRONG_full_name)
        self.assertRaises(AssertionError, assert_hybrid_attributes_are_consistent, Student.WRONG_magic_number1_times_n, n=3)

    def test_positional_args(self):
        self.assertHybridAttributesAreConsistent(Student.magic_number1_times_n, 3)
        assert_hybrid_attributes_are_consistent(Student.magic_number1_times_n, 3)

    def test_keyword_args(self):
        self.assertHybridAttributesAreConsistent(Student.magic_number1_times_n, n=3)
        assert_hybrid_attributes_are_consistent(Student.magic_number1_times_n, n=3)

    def test_queryset(self):
        # No AssertionError raised as it respected the queryset parameter (which in this case ran the sanity check for no items).
        self.assertHybridAttributesAreConsistent(Student.WRONG_full_name, queryset=Student.objects.none())
        self.assertHybridAttributesAreConsistent(Student.WRONG_magic_number1_times_n, n=3, queryset=Student.objects.none())
        assert_hybrid_attributes_are_consistent(Student.WRONG_full_name, queryset=Student.objects.none())
        assert_hybrid_attributes_are_consistent(Student.WRONG_magic_number1_times_n, n=3, queryset=Student.objects.none())
