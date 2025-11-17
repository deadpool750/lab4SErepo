from django.test import TestCase
from medtrackerapp.models import Medication, DoseLog
from django.utils import timezone
from datetime import timedelta, datetime
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError


class MedicationModelTests(TestCase):

    def test_str_returns_name_and_dosage(self):
        """
        Test that the string representation of the model is correct.
        """
        med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)
        self.assertEqual(str(med), "Aspirin (100mg)")

    def test_medication_positive_creation(self):
        """
        Test that a medication can be created with valid data.
        (This is similar to the setUp in the DoseLog tests)
        """
        med = Medication.objects.create(
            name="Paracetamol",
            dosage_mg=500,
            prescribed_per_day=3
        )
        self.assertEqual(med.name, "Paracetamol")
        self.assertEqual(med.dosage_mg, 500)
        self.assertEqual(med.prescribed_per_day, 3)

    def test_medication_negative_dosage(self):
        """
        Test that creating a medication with a negative dosage_mg
        raises a validation error.
        """
        with self.assertRaises((ValidationError, IntegrityError)):
            med = Medication.objects.create(
                name="BadIbuprofen",
                dosage_mg=-400,  # Invalid data
                prescribed_per_day=3
            )
            med.full_clean()

    def test_medication_missing_name(self):
        """
        Test that creating a medication with no name
        raises a validation error.
        """
        with self.assertRaises((ValidationError, IntegrityError)):
            med = Medication.objects.create(
                dosage_mg=200,
                prescribed_per_day=1
            )
            med.full_clean()


class TestDoseLog(TestCase):

    def setUp(self):
        """
        Set up a medication that can be used by all test methods
        in this class.
        """
        self.med = Medication.objects.create(
            name="Paracetamol",
            dosage_mg=500,
            prescribed_per_day=3
        )

    def test_log_dose_positive(self):
        """
        Test a positive path: logging a dose.
        """
        log_time = timezone.now()
        log = DoseLog.objects.create(
            medication=self.med,
            taken_at=log_time  # <-- This is the corrected field name
        )

        # Check that the object was created and fields are correct
        self.assertEqual(log.medication, self.med)
        self.assertEqual(log.taken_at, log_time)

    def test_log_dose_missing_medication(self):
        """
        Test a negative path: trying to create a log
        without linking it to a medication.
        """
        with self.assertRaises((ValidationError, IntegrityError)):
            log = DoseLog.objects.create(
                taken_at=timezone.now()  # <-- This is the corrected field name
            )
            log.full_clean()