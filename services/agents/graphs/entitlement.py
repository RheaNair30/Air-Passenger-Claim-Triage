
REQUIRED_PROVISIONS = {
    "flight_cancellation_compensation": ["3.3.2"],
    "meals_and_refreshments": ["3.3.2", "3.8.1"],
}


def _find_provision_evidence(
    provision: str,
    retrieved_evidence: list[dict],
) -> list[dict]:
    """Find retrieved DGCA passages containing the required clause reference."""
    return [
        item
        for item in retrieved_evidence
        if item.get("document_type") == "dgca_regulation"
        and provision in item.get("content", "")
    ]


def assess_entitlements(
    claim: dict,
    retrieved_evidence: list[dict],
) -> dict:
    """
    Assess separate entitlement heads for the mandatory cancellation case.

    This is a limited initial rule set, not a general legal decision engine.
    Every required provision must be present in retrieved evidence before
    the recommendation can proceed to verification.
    """
    disruption = claim.get("disruption", {})
    disruption_type = disruption.get("claimed_type")
    alternate_accepted = disruption.get("alternate_flight_accepted")

    if disruption_type != "cancellation":
        return {
            "status": "further_evidence_required",
            "reason": "This rule set currently covers cancellation claims only.",
            "entitlement_heads": [],
            "evidence": retrieved_evidence,
        }

    if alternate_accepted is not True:
        return {
            "status": "further_evidence_required",
            "reason": (
                "The mandatory-case rule requires confirmation that "
                "the passenger accepted the alternate flight."
            ),
            "entitlement_heads": [],
            "evidence": retrieved_evidence,
        }

    decisions = [
        {
            "head": "flight_cancellation_compensation",
            "decision": "not_payable",
            "basis": (
                "The passenger accepted the alternate flight. "
                "For the specified mandatory demonstration case, "
                "compensation is therefore not payable under CAR 3.3.2."
            ),
            "provisions": REQUIRED_PROVISIONS[
                "flight_cancellation_compensation"
            ],
        },
        {
            "head": "meals_and_refreshments",
            "decision": "payable",
            "basis": (
                "Accepting the alternate flight does not remove the "
                "passenger's entitlement to meals and refreshments "
                "while waiting, under the applicable facilities provisions."
            ),
            "provisions": REQUIRED_PROVISIONS["meals_and_refreshments"],
        },
    ]

    assessed_heads = []
    missing_provisions = []

    for item in decisions:
        supporting_evidence = []
        missing_for_head = []

        for provision in item["provisions"]:
            matches = _find_provision_evidence(
                provision,
                retrieved_evidence,
            )

            if matches:
                supporting_evidence.extend(matches)
            else:
                missing_for_head.append(provision)
                missing_provisions.append(provision)

        assessed_heads.append({
            **item,
            "evidence": supporting_evidence,
            "evidence_complete": not missing_for_head,
            "missing_provisions": missing_for_head,
        })

    if missing_provisions:
        return {
            "status": "evidence_incomplete",
            "reason": (
                "Required provisions were not found in retrieved evidence. "
                "The recommendation must not be returned as verified."
            ),
            "missing_provisions": sorted(set(missing_provisions)),
            "entitlement_heads": assessed_heads,
            "evidence": retrieved_evidence,
        }

    return {
        "status": "assessed",
        "claim_reference": claim.get("client_reference"),
        "entitlement_heads": assessed_heads,
        "evidence": retrieved_evidence,
    }
