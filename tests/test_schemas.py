import pytest
from pydantic import ValidationError

from app.models.schemas import LeadPayload


def test_valid_lead():
    lead = LeadPayload(name="Иван", phone="+7 (900) 123-45-67", source="form")
    assert lead.phone == "9001234567"


def test_invalid_phone_raises():
    with pytest.raises(ValidationError):
        LeadPayload(name="Иван", phone="123", source="form")


def test_empty_name_raises():
    with pytest.raises(ValidationError):
        LeadPayload(name="   ", phone="9001234567", source="form")
