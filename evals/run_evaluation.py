
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pydantic import ValidationError

from common.schemas.claim import ClaimInput
from services.agents.graphs.claim_workflow import claim_workflow


def valid_claim():
    departure = datetime(2026, 12, 1, 10, 0, tzinfo=timezone.utc)

    return {
        "client_reference": "EVAL-E01",
        "narrative": (
            "My flight was cancelled with 90 minutes notice. "
            "I accepted an alternate flight departing four hours "
            "after my original scheduled departure."
        ),
        "passenger": {
            "name": "Evaluation Passenger",
            "email": "evaluation@example.com",
        },
        "booking_contact_provided": "yes",
        "pnr": "ABC123",
        "flight": {
            "airline_iata": "AI",
            "number": "101",
            "origin": "BLR",
            "destination": "DEL",
            "scheduled_departure": departure.isoformat(),
            "scheduled_arrival": (
                departure + timedelta(hours=3)
            ).isoformat(),
            "sector": "domestic",
        },
        "disruption": {
            "claimed_type": "cancellation",
            "notice_hours_before_departure": 1.5,
            "alternate_flight_offered": True,
            "alternate_flight_accepted": True,
            "alternate_departure": (
                departure + timedelta(hours=4)
            ).isoformat(),
            "stated_cause": "unknown",
        },
        "fare": {
            "basic_fare_inr": "5000",
            "fuel_charge_inr": "1000",
            "ticket_total_inr": "6000",
        },
    }


def check_schema_missing_passenger_name():
    claim = valid_claim()
    claim["passenger"].pop("name")

    try:
        ClaimInput.model_validate(claim)
        return False, "Claim unexpectedly passed validation"
    except ValidationError:
        return True, "Missing passenger name rejected"


def check_schema_missing_pnr():
    claim = valid_claim()
    claim.pop("pnr")

    try:
        ClaimInput.model_validate(claim)
        return False, "Claim unexpectedly passed validation"
    except ValidationError:
        return True, "Missing PNR rejected"


def check_mandatory_cancellation():
    claim = ClaimInput.model_validate(valid_claim()).model_dump(
        mode="json"
    )

    initial_state = {
        "claim": claim,
        "disruption_type": "unspecified",
        "notice_hours": None,
        "alternate_accepted": False,
        "investigation_notes": [],
        "retrieved_evidence": [],
        "status": "started",
        "assessment": {},
        "verified_result": {},
        "investigation_summary": "",
        "tool_calls": [],
        "investigation_attempts": 0,
    }

    result = claim_workflow.invoke(initial_state)
    verified = result.get("verified_result", {})

    heads = {
        item.get("head"): item
        for item in verified.get("entitlement_heads", [])
    }

    compensation = heads.get("flight_cancellation_compensation", {})
    meals = heads.get("meals_and_refreshments", {})

    passed = (
        verified.get("status") == "verified"
        and compensation.get("decision") == "not_payable"
        and meals.get("decision") == "payable"
        and compensation.get("verified") is True
        and meals.get("verified") is True
    )

    return passed, (
        f"Workflow status: {verified.get('status')}; "
        f"compensation: {compensation.get('decision')}; "
        f"meals: {meals.get('decision')}"
    )

def check_unspecified_disruption():
    claim = valid_claim()
    claim["disruption"]["claimed_type"] = "unspecified"

    try:
        ClaimInput.model_validate(claim)
        return True, "Unspecified disruption accepted by schema"
    except ValidationError as error:
        return False, str(error)


def check_invalid_fare():
    claim = valid_claim()
    claim["fare"]["basic_fare_inr"] = "5000"
    claim["fare"]["fuel_charge_inr"] = "2000"
    claim["fare"]["ticket_total_inr"] = "6000"

    try:
        ClaimInput.model_validate(claim)
        return False, "Invalid fare unexpectedly passed validation"
    except ValidationError:
        return True, "Invalid fare rejected"

def check_invalid_datetime():
    claim = valid_claim()
    claim["flight"]["scheduled_departure"] = "2026-12-01T10:00:00"

    try:
        ClaimInput.model_validate(claim)
        return False, "Timezone-naive datetime unexpectedly accepted"
    except ValidationError:
        return True, "Datetime without timezone rejected"

def main():
    tests = [
        ("E01", "Mandatory cancellation workflow", check_mandatory_cancellation),
        ("E02", "Missing passenger name", check_schema_missing_passenger_name),
        ("E03", "Missing PNR", check_schema_missing_pnr),
        ("E04", "Unspecified disruption", check_unspecified_disruption),
        ("B2", "Missing datetime timezone", check_invalid_datetime),
        ("B4", "Invalid fare total", check_invalid_fare),
    ]

    results = []

    for scenario_id, name, test in tests:
        try:
            passed, details = test()
        except Exception as error:
            passed = False
            details = f"{type(error).__name__}: {error}"

        results.append({
            "id": scenario_id,
            "scenario": name,
            "passed": passed,
            "details": details,
        })

        print(
            f"[{'PASS' if passed else 'FAIL'}] "
            f"{scenario_id}: {name} — {details}"
        )

    passed_count = sum(item["passed"] for item in results)

    report = {
        "total": len(results),
        "passed": passed_count,
        "failed": len(results) - passed_count,
        "results": results,
    }

    output_path = Path(__file__).parent / "evaluation_results.json"
    output_path.write_text(json.dumps(report, indent=2))

    print(f"\nEvaluation: {passed_count}/{len(results)} passed")
    print(f"Report saved to: {output_path}")


if __name__ == "__main__":
    main()
