
from datetime import datetime
from copy import deepcopy

import pytest
from pydantic import ValidationError

from common.schemas.claim import ClaimInput


def valid_claim():
    return {
        "narrative": "My flight was cancelled and I was offered an alternate flight.",
        "passenger": {
            "name": "Test Passenger",
            "email": "passenger@example.com",
        },
        "pnr": "ABC123",
        "flight": {
            "airline_iata": "AI",
            "number": "101",
            "origin": "BLR",
            "destination": "DEL",
            "scheduled_departure": "2026-11-15T10:00:00+05:30",
            "scheduled_arrival": "2026-11-15T12:45:00+05:30",
            "sector": "domestic",
        },
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("narrative", ""),
        ("narrative", "   "),
        ("pnr", "ABC12"),
        ("pnr", "ABC12!"),
        ("passenger", None),
        ("passenger.name", ""),
        ("passenger.email", "not-an-email"),
        ("passenger.phone", "123-ABC"),
        ("flight.airline_iata", "A"),
        ("flight.number", "ABCDE"),
        ("flight.origin", "BL"),
        ("flight.destination", "123"),
        ("flight.scheduled_departure", "2026-11-15T10:00:00"),
        ("flight.block_time_minutes_stated", -10),
        ("disruption.delay_minutes", -5),
        ("fare.basic_fare_inr", -100),
        ("unexpected_field", "not allowed"),
    ],
)
def test_invalid_claims_are_rejected(field, value):
    data = valid_claim()

    if "." in field:
        parent, child = field.split(".", 1)

        if parent not in data:
            data[parent] = {}

        if value is None:
            data[parent] = None
        else:
            data[parent][child] = value

    elif field == "unexpected_field":
        data[field] = value

    else:
        data[field] = value

    with pytest.raises(ValidationError):
        ClaimInput.model_validate(data)


def test_valid_claim_is_accepted():
    claim = ClaimInput.model_validate(valid_claim())

    assert claim.pnr == "ABC123"
    assert claim.flight.airline_iata == "AI"
    assert claim.flight.origin == "BLR"


def test_mandatory_cancellation_scenario_can_be_submitted():
    data = valid_claim()

    data["narrative"] = (
        "Flight cancelled. Passenger notified 90 minutes before "
        "departure, accepted an alternate flight departing four "
        "hours after the original scheduled departure."
    )

    data["disruption"] = {
        "claimed_type": "cancellation",
        "notified_at": "2026-11-15T08:30:00+05:30",
        "notice_hours_before_departure": 1.5,
        "alternate_flight_offered": True,
        "alternate_flight_accepted": True,
        "alternate_departure": "2026-11-15T14:00:00+05:30",
    }

    claim = ClaimInput.model_validate(data)

    assert claim.disruption.claimed_type == "cancellation"
    assert claim.disruption.alternate_flight_accepted is True


def test_optional_disruption_details_can_be_omitted():
    claim = ClaimInput.model_validate(valid_claim())

    assert claim.disruption.claimed_type.value == "unspecified"
    assert claim.disruption.stated_cause.value == "unknown"


def test_origin_and_destination_must_differ():
    data = valid_claim()
    data["flight"]["destination"] = "BLR"

    with pytest.raises(ValidationError, match="B1"):
        ClaimInput.model_validate(data)


def test_arrival_must_follow_departure():
    data = valid_claim()
    data["flight"]["scheduled_arrival"] = (
        "2026-11-15T09:00:00+05:30"
    )

    with pytest.raises(ValidationError, match="B2"):
        ClaimInput.model_validate(data)


def test_alternate_acceptance_requires_offer():
    data = valid_claim()
    data["disruption"] = {
        "alternate_flight_accepted": True,
    }

    with pytest.raises(ValidationError, match="B3"):
        ClaimInput.model_validate(data)


def test_ticket_total_cannot_be_below_components():
    data = valid_claim()
    data["fare"] = {
        "basic_fare_inr": "5000",
        "fuel_charge_inr": "1000",
        "ticket_total_inr": "4000",
    }

    with pytest.raises(ValidationError, match="B4"):
        ClaimInput.model_validate(data)