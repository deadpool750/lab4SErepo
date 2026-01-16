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
        # initializing base medication instance for reuse in multiple test cases
        self.med = Medication.objects.create(
            name="Aspirin", dosage_mg=100, prescribed_per_day=2
        )
        # storing list endpoint url for medication retrieval
        self.list_url = reverse("medication-list")
        # storing detail endpoint url for specific medication operations
        self.detail_url = reverse("medication-detail", kwargs={"pk": self.med.pk})

    def test_list_medications_valid(self):
        # sending get request to retrieve medication list
        response = self.client.get(self.list_url)
        # asserting successful response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # verifying returned list size
        self.assertEqual(len(response.data), 1)
        # confirming medication name matches expected
        self.assertEqual(response.data[0]["name"], "Aspirin")

    def test_create_medication_valid(self):
        # preparing valid medication payload for post request
        data = {"name": "Paracetamol", "dosage_mg": 500, "prescribed_per_day": 3}
        # sending post request to create medication
        response = self.client.post(self.list_url, data)
        # verifying creation success
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # ensuring total count increased
        self.assertEqual(Medication.objects.count(), 2)
        # checking name matches input
        self.assertEqual(response.data["name"], "Paracetamol")

    def test_create_medication_invalid(self):
        # providing incomplete data payload lacking required fields
        data = {"name": "Ibuprofen"}
        # sending invalid post request
        response = self.client.post(self.list_url, data)
        # confirming rejection with appropriate status code
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # ensuring database count unchanged
        self.assertEqual(Medication.objects.count(), 1)

    def test_retrieve_medication_valid(self):
        # sending get request for existing medication
        response = self.client.get(self.detail_url)
        # verifying success
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # ensuring name matches expected
        self.assertEqual(response.data["name"], "Aspirin")

    def test_retrieve_medication_invalid(self):
        # preparing url for nonexistent medication id
        invalid_url = reverse("medication-detail", kwargs={"pk": 999})
        # executing get request
        response = self.client.get(invalid_url)
        # verifying not found response
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_medication_valid(self):
        # payload for updating an existing medication
        data = {"name": "Aspirin Updated", "dosage_mg": 150, "prescribed_per_day": 2}
        # sending put request
        response = self.client.put(self.detail_url, data)
        # checking update success
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # confirming updated value in response
        self.assertEqual(response.data["dosage_mg"], 150)
        # refreshing instance from database
        self.med.refresh_from_db()
        # verifying updated dosage value
        self.assertEqual(self.med.dosage_mg, 150)

    def test_delete_medication_valid(self):
        # issuing delete request to remove medication
        response = self.client.delete(self.detail_url)
        # checking for success status without content
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # confirming removal from database
        self.assertEqual(Medication.objects.count(), 0)


class DoseLogViewTests(APITestCase):
    def setUp(self):
        # setting up base medication for log associations
        self.med = Medication.objects.create(
            name="Aspirin", dosage_mg=100, prescribed_per_day=2
        )
        # referencing log list endpoint
        self.log_list_url = reverse("doselog-list")

    def test_create_log_valid(self):
        # providing valid payload for dose log creation
        data = {"medication": self.med.pk, "taken_at": timezone.now()}
        # sending post request to create log
        response = self.client.post(self.log_list_url, data)
        # confirming successful creation
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # checking log count increment
        self.assertEqual(DoseLog.objects.count(), 1)
        # verifying medication association
        self.assertEqual(response.data["medication"], self.med.pk)

    def test_create_log_invalid(self):
        # sending log creation without medication reference
        data = {"taken_at": timezone.now()}
        response = self.client.post(self.log_list_url, data)
        # expecting failure for missing required field
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # confirming no logs added
        self.assertEqual(DoseLog.objects.count(), 0)

    def test_list_logs_valid(self):
        # creating dose log instance for testing retrieval
        DoseLog.objects.create(medication=self.med, taken_at=timezone.now())
        # requesting list of logs
        response = self.client.get(self.log_list_url)
        # ensuring successful retrieval
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # checking list size
        self.assertEqual(len(response.data), 1)


class DoseLogFilterViewTests(APITestCase):
    def setUp(self):
        # initializing medication for testing filter operations
        self.med = Medication.objects.create(
            name="Aspirin", dosage_mg=100, prescribed_per_day=2
        )
        # referencing logs list endpoint
        self.log_list_url = reverse("doselog-list")
        # defining custom filter endpoint path
        self.log_filter_url = "/api/logs/filter/"

    def test_create_log_valid(self):
        # valid payload for creating a log entry
        data = {"medication": self.med.pk, "taken_at": timezone.now()}
        # performing post request
        response = self.client.post(self.log_list_url, data)
        # validating correct creation
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # ensuring log exists
        self.assertEqual(DoseLog.objects.count(), 1)
        # checking response medication id
        self.assertEqual(response.data["medication"], self.med.pk)

    def test_create_log_invalid(self):
        # invalid payload without medication id
        data = {"taken_at": timezone.now()}
        response = self.client.post(self.log_list_url, data)
        # ensuring request fails appropriately
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # verifying no logs created
        self.assertEqual(DoseLog.objects.count(), 0)

    def test_list_logs_valid(self):
        # generating a log entry for test retrieval
        DoseLog.objects.create(medication=self.med, taken_at=timezone.now())
        # requesting log list
        response = self.client.get(self.log_list_url)
        # checking for correct response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # confirming one entry returned
        self.assertEqual(len(response.data), 1)

    def test_filter_logs_by_date_range_valid(self):
        # establishing date variables for filtering
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        # converting dates to timezone-aware datetimes
        yesterday_time = timezone.make_aware(
            datetime.combine(yesterday, datetime.min.time())
        )
        today_time = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        tomorrow_time = timezone.make_aware(
            datetime.combine(tomorrow, datetime.min.time())
        )
        # creating dose logs for testing filter accuracy
        DoseLog.objects.create(medication=self.med, taken_at=yesterday_time)
        DoseLog.objects.create(medication=self.med, taken_at=today_time)
        DoseLog.objects.create(medication=self.med, taken_at=tomorrow_time)
        # preparing date range parameters
        params = {"start": yesterday.isoformat(), "end": today.isoformat()}
        # issuing get request with filtering parameters
        response = self.client.get(self.log_filter_url, params)
        # checking successful filtering
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # verifying filtered log count matches expectation
        self.assertEqual(len(response.data), 2)

    def test_filter_logs_invalid_params(self):
        # using invalid end date format to test failure case
        params = {
            "start": timezone.now().date().isoformat(),
            "end": "this-is-not-a-date",
        }
        # sending request with invalid parameters
        response = self.client.get(self.log_filter_url, params)
        # expecting bad request response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DrugInfoServiceTests(APITestCase):
    def setUp(self):
        # creating base medication for info retrieval tests
        self.med = Medication.objects.create(
            name="Aspirin", dosage_mg=100, prescribed_per_day=2
        )
        # storing endpoint for drug info lookup
        self.info_url = f"/api/medications/{self.med.pk}/info/"

    @patch("medtrackerapp.services.requests.get")
    def test_drug_info_service_mocked(self, mock_requests_get):
        # setting up mocked external api response for controlled test conditions
        fake_api_response = {
            "results": [
                {
                    "openfda": {
                        "generic_name": ["Aspirin"],
                        "manufacturer_name": ["Bayer"],
                    },
                    "warnings": ["Test warning"],
                    "purpose": ["Test purpose"],
                }
            ]
        }
        # configuring mock to.return_value.status and response json
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = fake_api_response
        # making request to drug info endpoint
        response = self.client.get(self.info_url)
        # validating proper handling and response data extraction
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_requests_get.assert_called_once()
        self.assertEqual(response.data["manufacturer"], "Bayer")
        self.assertEqual(response.data["warnings"], ["Test warning"])
        self.assertEqual(response.data["purpose"], ["Test purpose"])
        self.assertEqual(response.data["name"], "Aspirin")

    @patch("medtrackerapp.services.requests.get")
    def test_drug_info_service_api_error(self, mock_requests_get):
        # simulating api failure with non-200 status
        mock_requests_get.return_value.status_code = 404
        mock_requests_get.return_value.json.return_value = {"error": "Not Found"}
        # calling endpoint expecting error
        response = self.client.get(self.info_url)
        # validating returned status for upstream error
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)

    @patch("medtrackerapp.services.requests.get")
    def test_drug_info_service_no_results(self, mock_requests_get):
        # faking api returning empty results list
        fake_api_response = {"results": []}
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = fake_api_response
        # requesting drug info
        response = self.client.get(self.info_url)
        # expecting bad gateway due to no results
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)


class DirectServiceTests(TestCase):
    def test_service_no_drug_name(self):
        # triggering validation error for none drug_name input
        with self.assertRaisesRegex(ValueError, "drug_name is required"):
            DrugInfoService.get_drug_info(drug_name=None)

        # triggering validation error for empty string input
        with self.assertRaisesRegex(ValueError, "drug_name is required"):
            DrugInfoService.get_drug_info(drug_name="")


class MedicationExpectedDosesTest(APITestCase):
    def setUp(self):
        # creating a sample medication for testing using your model's fields
        self.medication = Medication.objects.create(
            name="Test Med", dosage_mg=10, prescribed_per_day=2
        )
        self.url = reverse("medication-expected-doses", args=[self.medication.id])

    def test_expected_doses_valid(self):
        """Test legitimate request returns 200 and correct calculation"""
        # request with ?days=10
        response = self.client.get(self.url, {"days": 10})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["medication_id"], self.medication.id)
        self.assertEqual(response.data["days"], 10)
        self.assertIn("expected_doses", response.data)

    def test_expected_doses_missing_param(self):
        """Test missing 'days' parameter returns 400"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expected_doses_invalid_param(self):
        """Test invalid 'days' (negative or string) returns 400"""
        response = self.client.get(self.url, {"days": -5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get(self.url, {"days": "invalid"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
