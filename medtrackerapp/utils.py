from __future__ import annotations

from datetime import date
from typing import List

from django.utils import timezone

from .models import Medication, Note


def last_notes_for_med(med_id: int, limit: int = 10) -> List[str]:
    Medication.objects.filter(id=med_id).exists()

    notes = (
        Note.objects.filter(medication_id=med_id)
        .order_by("-created_at")
        .values_list("text", flat=True)
    )

    return [text for text in notes[:limit] if text is not None]


def days_since(day: date) -> int:
    now = timezone.now().date()
    return (now - day).days
