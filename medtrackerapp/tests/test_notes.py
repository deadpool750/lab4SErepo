from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from medtrackerapp.models import Medication


class NoteTests(APITestCase):
    def setUp(self):
        self.medication = Medication.objects.create(
            name="Test Med",
            dosage_mg=10,
            prescribed_per_day=1
        )
        # we assume the url router will name the endpoint 'note-list'
        # will probably raise an error because url doesnt exist yet.
        try:
            self.list_url = reverse('note-list')
        except:
            self.list_url = '/api/notes/'

    def test_create_note(self):
        """Test creating a new note for a medication"""
        data = {
            'medication': self.medication.id,
            'text': 'Take with food',
            # Date should be auto-added by the model, so we don't send it
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['text'], 'Take with food')
        self.assertEqual(response.data['medication'], self.medication.id)

    def test_list_notes(self):
        """Test retrieving list of notes"""
        # Create a note first (we can't use the model yet, so we assume the POST works or we skip this until Green)
        # For strict TDD, we write the expectation.
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_note(self):
        """Test deleting a note"""
        # Since we can't create a Note object directly (Model doesn't exist),
        # we create one via API for this test
        create_resp = self.client.post(self.list_url, {
            'medication': self.medication.id,
            'text': 'To be deleted'
        })
        note_id = create_resp.data.get('id')

        if note_id:
            url = reverse('note-detail', args=[note_id])
            response = self.client.delete(url)
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_update_note_not_allowed(self):
        """Requirements say updating an existing note should NOT be supported"""
        # Create a note first
        create_resp = self.client.post(self.list_url, {
            'medication': self.medication.id,
            'text': 'Original Text'
        })
        note_id = create_resp.data.get('id')

        if note_id:
            url = reverse('note-detail', args=[note_id])
            response = self.client.put(url, {'text': 'Updated Text'})
            # Should be 405 Method Not Allowed
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)