from django.test import TestCase
from medtrackerapp.models import Medication, DoseLog
from django.utils import timezone
from datetime import timedelta, datetime, date
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError


class MedicationModelTests(TestCase):

    def setUp(self):
        """Set up a standard medication for use in tests."""
        self.med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=2
        )

    def test_str_returns_name_and_dosage(self):
        """Test the string representation of the Medication model."""
        self.assertEqual(str(self.med), "Aspirin (100mg)")

    def test_medication_positive_creation(self):
        """Test that a medication can be created with valid data."""
        med = Medication.objects.create(
            name="Paracetamol",
            dosage_mg=500,
            prescribed_per_day=3
        )
        self.assertEqual(med.name, "Paracetamol")
        self.assertEqual(med.dosage_mg, 500)

    def test_medication_negative_dosage(self):
        """Test creating a medication with invalid negative dosage."""
        with self.assertRaises((ValidationError, IntegrityError)):
            med = Medication.objects.create(
                name="BadIbuprofen",
                dosage_mg=-400,
                prescribed_per_day=3
            )
            med.full_clean()

    def test_medication_missing_name(self):
        """Test creating a medication with no name."""
        with self.assertRaises((ValidationError, IntegrityError)):
            med = Medication.objects.create(
                dosage_mg=200,
                prescribed_per_day=1
            )
            med.full_clean()


    def test_adherence_rate_no_logs(self):
        """
        Test adherence_rate method (line 35) when no logs exist.
        """
        self.assertEqual(self.med.adherence_rate(), 0.0)

    def test_adherence_rate_mixed_logs(self):
        """
        Test adherence_rate method (lines 37-38) with mixed logs.
        """
        now = timezone.now()
        DoseLog.objects.create(medication=self.med, taken_at=now, was_taken=True)
        DoseLog.objects.create(medication=self.med, taken_at=now - timedelta(days=1), was_taken=False)
        DoseLog.objects.create(medication=self.med, taken_at=now - timedelta(days=2), was_taken=True)

        self.assertEqual(self.med.adherence_rate(), 66.67)

    def test_expected_doses_valid(self):
        """
        Test expected_doses method (line 54) for a valid case.
        """
        # 2 (prescribed_per_day) * 10 (days) = 20
        self.assertEqual(self.med.expected_doses(days=10), 20)

    def test_expected_doses_invalid_days(self):
        """
        Test expected_doses method (line 53) for negative days.
        """
        with self.assertRaisesRegex(ValueError, "Days and schedule must be positive"):
            self.med.expected_doses(days=-5)

    def test_expected_doses_invalid_schedule(self):
        """
        Test expected_doses method (line 53) for zero schedule.
        """
        med_zero = Medication.objects.create(name="Placebo", dosage_mg=0, prescribed_per_day=0)
        with self.assertRaisesRegex(ValueError, "Days and schedule must be positive"):
            med_zero.expected_doses(days=10)

    def test_adherence_rate_over_period_invalid_date(self):
        """
        Test adherence_rate_over_period (line 64) when start > end.
        """
        today = date.today()
        yesterday = today - timedelta(days=1)
        with self.assertRaisesRegex(ValueError, "start_date must be before or equal to end_date"):
            self.med.adherence_rate_over_period(start_date=today, end_date=yesterday)

    def test_adherence_rate_over_period_calculation(self):
        """
        Test adherence_rate_over_period (lines 66-81) calculation.
        """
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Create logs: one in range, one out of range
        now = timezone.now()
        DoseLog.objects.create(medication=self.med, taken_at=now, was_taken=True)  # In range
        DoseLog.objects.create(medication=self.med, taken_at=now - timedelta(days=2), was_taken=True)  # Out of range

        # Period is 2 days (yesterday, today). Expected = 2 * 2 = 4 doses
        # Taken = 1 (the one from 'now')
        # Adherence = (1 / 4) * 100 = 25.0
        adherence = self.med.adherence_rate_over_period(start_date=yesterday, end_date=today)
        self.assertEqual(adherence, 25.0)

    def test_fetch_external_info_exception(self):
        """
        Test fetch_external_info (line 105) catches exceptions.

        We can test this directly without a mock by calling it
        with a medication that will fail in the service (e.g., empty name).
        """
        # This medication has an empty name, which the service will reject
        med_invalid = Medication.objects.create(name="", dosage_mg=0, prescribed_per_day=1)
        result = med_invalid.fetch_external_info()
        self.assertIn("error", result)
        self.assertEqual(result["error"], "drug_name is required")


class TestDoseLog(TestCase):

    def setUp(self):
        """Set up a medication for DoseLog tests."""
        self.med = Medication.objects.create(
            name="Paracetamol",
            dosage_mg=500,
            prescribed_per_day=3
        )

    def test_log_dose_positive(self):
        """Test a positive path: logging a dose."""
        log_time = timezone.now()
        log = DoseLog.objects.create(
            medication=self.med,
            taken_at=log_time
        )
        self.assertEqual(log.medication, self.med)
        self.assertEqual(log.taken_at, log_time)
        self.assertTrue(log.was_taken)  # Check default value

    def test_log_dose_missing_medication(self):
        """Test a negative path: creating a log without medication."""
        with self.assertRaises((ValidationError, IntegrityError)):
            log = DoseLog.objects.create(
                taken_at=timezone.now()
            )
            log.full_clean()

    # --- New Tests for Code Coverage ---

    def test_dose_log_str_taken(self):
        """
        Test DoseLog __str__ method (lines 111-113) for a 'Taken' log.
        """
        log_time = timezone.make_aware(datetime(2025, 1, 1, 9, 30))
        log = DoseLog.objects.create(
            medication=self.med,
            taken_at=log_time,
            was_taken=True
        )
        # so we check for the components.
        expected_str = "Paracetamol at 2025-01-01 09:30 - Taken"
        self.assertEqual(str(log), expected_str)

    def test_dose_log_str_missed(self):
        """
        Test DoseLog __str__ method (lines 111-113) for a 'Missed' log.
        """
        log_time = timezone.make_aware(datetime(2025, 1, 2, 12, 0))
        log = DoseLog.objects.create(
            medication=self.med,
            taken_at=log_time,
            was_taken=False
        )
        expected_str = "Paracetamol at 2025-01-02 12:00 - Missed"
        self.assertEqual(str(log), expected_str)