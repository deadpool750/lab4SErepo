from rest_framework.test import APITestCase
from medtrackerapp.models import Medication, DoseLog
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from datetime import datetime, timedelta

class MedicationViewTests(APITestCase):
    def setUp(self):
        """
        Set up one initial medication for tests that need an existing object.
        """
        self.med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)
        self.list_url = reverse("medication-list")  # /api/medications/
        self.detail_url = reverse("medication-detail", kwargs={"pk": self.med.pk})  # /api/medications/1/

    def test_list_medications_valid(self):
        """
        Test GET /api/medications/
        Checks that the list endpoint returns a 200 OK and the data.
        """
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Aspirin")

    def test_create_medication_valid(self):
        """
        Test POST /api/medications/ (Positive Path)
        Checks that a new medication can be created.
        """
        data = {
            "name": "Paracetamol",
            "dosage_mg": 500,
            "prescribed_per_day": 3
        }
        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Medication.objects.count(), 2)  # The setUp med + this new one
        self.assertEqual(response.data["name"], "Paracetamol")

    def test_create_medication_invalid(self):
        """
        Test POST /api/medications/ (Negative Path)
        Checks that a 400 BAD REQUEST is returned for incomplete data.
        """
        data = {
            "name": "Ibuprofen"  # Missing required fields
        }
        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Medication.objects.count(), 1)  # No new object created

    def test_retrieve_medication_valid(self):
        """
        Test GET /api/medications/<id>/ (Positive Path)
        Checks that a single medication can be retrieved.
        """
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Aspirin")

    def test_retrieve_medication_invalid(self):
        """
        Test GET /api/medications/<id>/ (Negative Path - Invalid Endpoint)
        Checks that a 404 NOT FOUND is returned for a non-existent ID.
        """
        invalid_url = reverse("medication-detail", kwargs={"pk": 999})
        response = self.client.get(invalid_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_medication_valid(self):
        """
        Test PUT /api/medications/<id>/ (Positive Path)
        Checks that an existing medication can be updated.
        """
        data = {
            "name": "Aspirin Updated",
            "dosage_mg": 150,
            "prescribed_per_day": 2
        }
        response = self.client.put(self.detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["dosage_mg"], 150)
        self.med.refresh_from_db()
        self.assertEqual(self.med.dosage_mg, 150)

    def test_delete_medication_valid(self):
        """
        Test DELETE /api/medications/<id>/ (Positive Path)
        Checks that a medication can be deleted.
        """
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Medication.objects.count(), 0)



class DoseLogViewTests(APITestCase):
    def setUp(self):
        """
        Set up a medication to log doses against.
        """
        self.med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)
        self.log_list_url = reverse("doselog-list")

    def test_create_log_valid(self):
        """
        Test POST /api/logs/ (Positive Path)
        Checks that a new dose log can be created.
        """
        data = {
            "medication": self.med.pk,
            "taken_at": timezone.now()
        }
        response = self.client.post(self.log_list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DoseLog.objects.count(), 1)
        self.assertEqual(response.data["medication"], self.med.pk)

    def test_create_log_invalid(self):
        """
        Test POST /api/logs/ (Negative Path)
        Checks that a log cannot be created without a medication.
        """
        data = {
            "taken_at": timezone.now()
        }
        response = self.client.post(self.log_list_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(DoseLog.objects.count(), 0)

    def test_list_logs_valid(self):
        """
        Test GET /api/logs/ (Positive Path)
        Checks that the list of logs is returned.
        """
        DoseLog.objects.create(medication=self.med, taken_at=timezone.now())
        response = self.client.get(self.log_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class DoseLogViewTests(APITestCase):
    def setUp(self):
        """
        Set up a medication to log doses against.
        """
        self.med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)
        self.log_list_url = reverse("doselog-list")  # /api/logs/
        self.log_filter_url = "/api/logs/filter/"

    def test_create_log_valid(self):
        """
        Test POST /api/logs/ (Positive Path)
        Checks that a new dose log can be created.
        """
        data = {
            "medication": self.med.pk,
            "taken_at": timezone.now()
        }
        response = self.client.post(self.log_list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DoseLog.objects.count(), 1)
        self.assertEqual(response.data["medication"], self.med.pk)

    def test_create_log_invalid(self):
        """
        Test POST /api/logs/ (Negative Path)
        Checks that a log cannot be created without a medication.
        """
        data = {
            "taken_at": timezone.now()
        }
        response = self.client.post(self.log_list_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(DoseLog.objects.count(), 0)

    def test_list_logs_valid(self):
        """
        Test GET /api/logs/ (Positive Path)
        Checks that the list of logs is returned.
        """
        # Create a log first
        DoseLog.objects.create(medication=self.med, taken_at=timezone.now())

        response = self.client.get(self.log_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_logs_by_date_range_valid(self):
        """
        Test GET /api/logs/filter/ (Positive Path)
        Checks that logs can be filtered by a start and end date.
        """
        # --- Create test data ---
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        yesterday_time = timezone.make_aware(datetime.combine(yesterday, datetime.min.time()))
        today_time = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        tomorrow_time = timezone.make_aware(datetime.combine(tomorrow, datetime.min.time()))
        DoseLog.objects.create(medication=self.med, taken_at=yesterday_time)
        DoseLog.objects.create(medication=self.med, taken_at=today_time)
        DoseLog.objects.create(medication=self.med, taken_at=tomorrow_time)

        params = {
            'start': yesterday.isoformat(),  #e.g., "2025-11-16"
            'end': today.isoformat()  #e.g., "2025-11-17"
        }

        response = self.client.get(self.log_filter_url, params)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_logs_invalid_params(self):
        """
        Test GET /api/logs/filter/ (Negative Path)
        Checks that a 400 Bad Request is returned for invalid date formats.
        """
        params = {
            'start': timezone.now().date().isoformat(),
            'end': "this-is-not-a-date"
        }

        response = self.client.get(self.log_filter_url, params)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)