from rest_framework.test import APITestCase
from medtrackerapp.models import Medication, DoseLog
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from datetime import datetime, timedelta
from unittest.mock import patch
from medtrackerapp.services import DrugInfoService
from django.test import TestCase


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


class DrugInfoServiceTests(APITestCase):

    def setUp(self):
        self.med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)
        # This is the corrected URL path
        self.info_url = f"/api/medications/{self.med.pk}/info/"

    @patch('medtrackerapp.services.requests.get')
    def test_drug_info_service_mocked(self, mock_requests_get):
        """
        Test the /api/medications/<id>/info/ endpoint.
        This test mocks the external 'requests.get' call.
        """

        # --- 1. Setup the Mock ---
        # This is the FAKE raw data we pretend the external API sends.
        # It's designed to be processed by your DrugInfoService.
        fake_api_response = {
            "results": [
                {
                    "openfda": {
                        "generic_name": ["Aspirin"],
                        "manufacturer_name": ["Bayer"]
                    },
                    "warnings": ["Test warning"],
                    "purpose": ["Test purpose"]
                }
            ]
        }

        # Configure the mock to return the fake data
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = fake_api_response

        # --- 2. Run the Test ---
        # Call our API endpoint
        response = self.client.get(self.info_url)

        # --- 3. Check the Results ---
        # Check that our view returned 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that 'requests.get' was called by the service
        mock_requests_get.assert_called_once()

        # Check that the response.data IS the SIMPLE dictionary
        # returned by DrugInfoService, not the raw JSON.
        self.assertEqual(response.data['manufacturer'], "Bayer")
        self.assertEqual(response.data['warnings'], ["Test warning"])
        self.assertEqual(response.data['purpose'], ["Test purpose"])
        self.assertEqual(response.data['name'], "Aspirin")

    @patch('medtrackerapp.services.requests.get')
    def test_drug_info_service_api_error(self, mock_requests_get):
        """
        Tests the /info/ endpoint when the external API fails (e.g., 404).
        This should cover the error-handling path in the service.
        """
        # --- 1. Setup the Mock ---
        # Pretend the external API returns a 404 Not Found
        mock_requests_get.return_value.status_code = 404
        mock_requests_get.return_value.json.return_value = {"error": "Not Found"}

        # --- 2. Run the Test ---
        response = self.client.get(self.info_url)

        # --- 3. Check the Results ---
        # Check that our view caught the service's error and returned a
        # 502 Bad Gateway, as shown in your views.py
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)

    @patch('medtrackerapp.services.requests.get')
    def test_drug_info_service_no_results(self, mock_requests_get):
        """
        Tests the /info/ endpoint when the external API finds no results.
        This covers the 'No results found' error (line 69).
        """
        # --- 1. Setup the Mock ---
        # Pretend the external API returns 200 OK, but an empty results list
        fake_api_response = {
            "results": []  # Empty results
        }
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = fake_api_response

        # --- 2. Run the Test ---
        response = self.client.get(self.info_url)

        # --- 3. Check the Results ---
        # Our view should catch this and return a 502 Bad Gateway
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)


class DirectServiceTests(TestCase):

    def test_service_no_drug_name(self):
        """
        Tests the DrugInfoService directly to cover the
        'drug_name is required' validation (line 58).
        """
        # Test with None
        with self.assertRaisesRegex(ValueError, "drug_name is required"):
            DrugInfoService.get_drug_info(drug_name=None)

        # Test with an empty string
        with self.assertRaisesRegex(ValueError, "drug_name is required"):
            DrugInfoService.get_drug_info(drug_name="")

    @patch('medtrackerapp.services.requests.get')
    def test_drug_info_service_no_results(self, mock_requests_get):
        """
        Tests the /info/ endpoint when the external API finds no results.
        This covers the 'No results found' error (line 69).
        """
        # --- 1. Setup the Mock ---
        fake_api_response = {"results": []}  # Empty results
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = fake_api_response

        # --- 2. Run the Test ---
        response = self.client.get(self.info_url)

        # --- 3. Check the Results ---
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)


class DirectServiceTests(TestCase):

    def test_service_no_drug_name(self):
        """
        Tests the DrugInfoService directly to cover the
        'drug_name is required' validation (line 58).
        """
        # Test with None
        with self.assertRaisesRegex(ValueError, "drug_name is required"):
            DrugInfoService.get_drug_info(drug_name=None)

        # Test with an empty string
        with self.assertRaisesRegex(ValueError, "drug_name is required"):
            DrugInfoService.get_drug_info(drug_name="")