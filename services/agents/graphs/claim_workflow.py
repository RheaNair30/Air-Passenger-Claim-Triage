
from typing import TypedDict, Any

from langgraph.graph import StateGraph, END

from services.agents.graphs.investigation import investigation_graph
from services.agents.graphs.entitlement import assess_entitlements
from services.agents.graphs.verification import verify_entitlements


class ClaimWorkflowState(TypedDict):
    claim: dict
    disruption_type: str
    notice_hours: float | None
    alternate_accepted: bool
    investigation_notes: list[str]
    retrieved_evidence: list[dict]
    status: str
    assessment: dict
    verified_result: dict
    investigation_summary: str
    tool_calls: list[str]
    investigation_attempts: int





def run_investigation(state):
    result = investigation_graph.invoke({
        "claim": state["claim"],
        "disruption_type": state.get("disruption_type", "unspecified"),
        "notice_hours": state.get("notice_hours"),
        "alternate_accepted": state.get("alternate_accepted", False),
        "investigation_notes": [],
        "retrieved_evidence": [],
        "status": "started",
        "investigation_attempts": state.get("investigation_attempts", 0) + 1,
        "previous_summary": state.get("investigation_summary", ""),
    })

    return {
        "disruption_type": result.get("disruption_type", "unspecified"),
        "notice_hours": result.get("notice_hours"),
        "alternate_accepted": result.get("alternate_accepted", False),
        "investigation_notes": result.get("investigation_notes", []),
        "retrieved_evidence": result.get("retrieved_evidence", []),
        "investigation_summary": result.get("investigation_summary", ""),
        "tool_calls": result.get("tool_calls", []),
        "investigation_attempts": state.get("investigation_attempts", 0) + 1,
        "status": result.get("status", "evidence_incomplete"),
    }






def run_entitlement_assessment(state):
    if state.get("status") != "evidence_retrieved":
        assessment = {
            "status": "evidence_incomplete",
            "reason": (
                "The investigation did not retrieve sufficient evidence. "
                "An entitlement recommendation cannot be made."
            ),
            "entitlement_heads": [],
            "evidence": state.get("retrieved_evidence", []),
        }
        return {
            "assessment": assessment,
            "status": "evidence_incomplete",
        }

    assessment = assess_entitlements(
        state["claim"],
        state["retrieved_evidence"],
    )

    return {
        "assessment": assessment,
        "status": assessment["status"],
    }



def run_verification(state: ClaimWorkflowState):
    verified_result = verify_entitlements(state["assessment"])

    return {
        "verified_result": verified_result,
        "status": verified_result["status"],
    }

def route_after_investigation(state):
    if state.get("status") == "evidence_retrieved":
        return "assess"

    if state.get("investigation_attempts", 0) < 2:
        return "retry"

    return "escalate"


def escalate_incomplete_investigation(state):
    return {
        "verified_result": {
            "status": "escalation_required",
            "reason": (
                "Sufficient supporting evidence could not be retrieved "
                "after two investigation attempts."
            ),
            "entitlement_heads": [],
        },
        "status": "escalation_required",
    }



def build_claim_workflow():
    graph = StateGraph(ClaimWorkflowState)

    graph.add_node("investigation", run_investigation)
    graph.add_node("entitlement_assessment", run_entitlement_assessment)
    graph.add_node("verification", run_verification)
    graph.add_node("escalate", escalate_incomplete_investigation)

    graph.set_entry_point("investigation")

    graph.add_conditional_edges(
        "investigation",
        route_after_investigation,
        {
            "assess": "entitlement_assessment",
            "retry": "investigation",
            "escalate": "escalate",
        },
    )

    graph.add_edge("entitlement_assessment", "verification")
    graph.add_edge("verification", END)
    graph.add_edge("escalate", END)

    return graph.compile()


claim_workflow = build_claim_workflow()