
def verify_entitlements(assessment: dict) -> dict:
    """
    Verify that every entitlement head has retrieved evidence
    containing each cited DGCA clause.

    This is a deterministic citation-presence check. It does not
    claim to establish full semantic or legal correctness.
    """

    if assessment.get("status") != "assessed":
        return {
            "claim_reference": assessment.get("claim_reference"),
            "status": "escalation_required",
            "reason": (
                "The entitlement assessment is incomplete. "
                "An unassessed recommendation cannot be verified."
            ),
            "entitlement_heads": [],
        }

    verified_heads = []

    for head in assessment.get("entitlement_heads", []):
        citations = []
        unsupported_citations = []

        evidence = head.get("evidence", [])

        for provision in head.get("provisions", []):
            clause_number = provision.replace("DGCA CAR ", "").strip()

            matching_evidence = [
                item
                for item in evidence
                if item.get("document_type") == "dgca_regulation"
                and clause_number in item.get("content", "")
            ]

            if matching_evidence:
                citations.append({
                    "provision": provision,
                    "source_file": matching_evidence[0].get("source_file"),
                    "page": matching_evidence[0].get("page"),
                    "verified": True,
                })
            else:
                unsupported_citations.append(provision)

        head_verified = (
            head.get("evidence_complete", False)
            and not unsupported_citations
            and len(citations) == len(head.get("provisions", []))
        )

        verified_heads.append({
            "head": head.get("head"),
            "decision": (
                head.get("decision") if head_verified else "escalate"
            ),
            "basis": (
                head.get("basis") if head_verified else
                "The supporting citations could not be verified."
            ),
            "verified": head_verified,
            "citations": citations,
            "unsupported_citations": unsupported_citations,
        })

    all_verified = (
        bool(verified_heads)
        and all(head["verified"] for head in verified_heads)
    )

    return {
        "claim_reference": assessment.get("claim_reference"),
        "status": "verified" if all_verified else "escalation_required",
        "entitlement_heads": verified_heads,
    }
