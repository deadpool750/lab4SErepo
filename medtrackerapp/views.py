from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.dateparse import parse_date
from .models import Medication, DoseLog, Note
from .serializers import MedicationSerializer, DoseLogSerializer, NoteSerializer
from rest_framework.filters import SearchFilter

class MedicationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and managing medications.

    Provides standard CRUD operations via the Django REST Framework
    `ModelViewSet`, as well as a custom action for retrieving
    additional information from an external API (OpenFDA).

    Endpoints:
        - GET /medications/ — list all medications
        - POST /medications/ — create a new medication
        - GET /medications/{id}/ — retrieve a specific medication
        - PUT/PATCH /medications/{id}/ — update a medication
        - DELETE /medications/{id}/ — delete a medication
        - GET /medications/{id}/info/ — fetch external drug info from OpenFDA
    """
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer

    @action(detail=True, methods=["get"], url_path="info")
    def get_external_info(self, request, pk=None):
        """
        Retrieve external drug information from the OpenFDA API.

        Calls the `Medication.fetch_external_info()` method, which
        delegates to the `DrugInfoService` for API access.

        Args:
            request (Request): The current HTTP request.
            pk (int): Primary key of the medication record.

        Returns:
            Response:
                - 200 OK: External API data returned successfully.
                - 502 BAD GATEWAY: If the external API request failed.

        Example:
            GET /medications/1/info/
        """
        medication = self.get_object()
        data = medication.fetch_external_info()

        if isinstance(data, dict) and data.get("error"):
            return Response(data, status=status.HTTP_502_BAD_GATEWAY)
        return Response(data)

    @action(detail=True, methods=['get'], url_path='expected-doses')
    def expected_doses(self, request, pk=None):
        """
        Calculate the total number of doses required for a specific duration.

        Query Parameters:
            days (int): The number of days to calculate doses for. Must be positive.

        Returns:
            Response: JSON object containing medication_id, days, and expected_doses.
            400 Bad Request: If 'days' is missing, not an integer, or non-positive.
        """
        medication = self.get_object()
        days_param = request.query_params.get('days')

        # Check for presence first
        if not days_param:
            return Response(
                {"error": "The 'days' query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            days = int(days_param)
            # The model method handles logic and raises ValueError for non-positive days
            total_doses = medication.expected_doses(days)

        except (ValueError, TypeError):
            return Response(
                {"error": "The 'days' parameter must be a positive integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            "medication_id": medication.id,
            "days": days,
            "expected_doses": total_doses
        }, status=status.HTTP_200_OK)

class DoseLogViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and managing dose logs.

    A DoseLog represents an event where a medication dose was either
    taken or missed. This viewset provides standard CRUD operations
    and a custom filtering action by date range.

    Endpoints:
        - GET /logs/ — list all dose logs
        - POST /logs/ — create a new dose log
        - GET /logs/{id}/ — retrieve a specific log
        - PUT/PATCH /logs/{id}/ — update a dose log
        - DELETE /logs/{id}/ — delete a dose log
        - GET /logs/filter/?start=YYYY-MM-DD&end=YYYY-MM-DD —
          filter logs within a date range
    """
    queryset = DoseLog.objects.all()
    serializer_class = DoseLogSerializer

    @action(detail=False, methods=["get"], url_path="filter")
    def filter_by_date(self, request):
        """
        Retrieve all dose logs within a given date range.

        Query Parameters:
            - start (YYYY-MM-DD): Start date of the range (inclusive).
            - end (YYYY-MM-DD): End date of the range (inclusive).

        Returns:
            Response:
                - 200 OK: A list of dose logs between the two dates.
                - 400 BAD REQUEST: If start or end parameters are missing or invalid.

        Example:
            GET /logs/filter/?start=2025-11-01&end=2025-11-07
        """
        start = parse_date(request.query_params.get("start"))
        end = parse_date(request.query_params.get("end"))

        if not start or not end:
            return Response(
                {"error": "Both 'start' and 'end' query parameters are required and must be valid dates."},
                status=status.HTTP_400_BAD_REQUEST
            )

        logs = self.get_queryset().filter(
            taken_at__date__gte=start,
            taken_at__date__lte=end
        ).order_by("taken_at")

        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)


class NoteViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Doctor's Notes .

    Provides standard CRUD operations but strictly forbids updates
    to ensure the historical integrity of medical notes.
    """
    queryset = Note.objects.all()
    serializer_class = NoteSerializer

    filter_backends = (SearchFilter,)
    search_fields = ["medication__name"]

    def update(self, request, *args, **kwargs):
        """Override to disable full updates (PUT)."""
        return self._handle_update_attempt()

    def partial_update(self, request, *args, **kwargs):
        """Override to disable partial updates (PATCH)."""
        return self._handle_update_attempt()

    def _handle_update_attempt(self):
        """Helper method to return a standard 405 error for update attempts."""
        return Response(
            {"error": "Updates to doctor's notes are not supported."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

