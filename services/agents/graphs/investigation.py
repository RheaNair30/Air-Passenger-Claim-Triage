
from typing import TypedDict

from langgraph.graph import StateGraph, END

from services.agents.tools.retrieval_tool import search_claim_corpus
from services.agents.graphs.investigation_agent import run_investigation_agent


class InvestigationState(TypedDict):
    claim: dict
    disruption_type: str
    notice_hours: float | None
    alternate_accepted: bool
    investigation_notes: list[str]
    retrieved_evidence: list[dict]
    status: str
    investigation_summary: str
    tool_calls: list[str]
    investigation_attempts: int
    previous_summary: str


def extract_claim_facts(state: InvestigationState):
    claim = state["claim"]
    disruption = claim.get("disruption", {})

    notes = [
        f"Claim reference: {claim.get('client_reference')}",
        f"Disruption type: {disruption.get('claimed_type', 'unspecified')}",
        f"Notice before departure: {disruption.get('notice_hours_before_departure')} hours",
        f"Alternate flight accepted: {disruption.get('alternate_flight_accepted')}",
    ]

    return {
        "disruption_type": disruption.get("claimed_type", "unspecified"),
        "notice_hours": disruption.get("notice_hours_before_departure"),
        "alternate_accepted": disruption.get("alternate_flight_accepted", False),
        "investigation_notes": notes,
        "status": "facts_extracted",
    }




def retrieve_evidence(state):
    attempt = state.get("investigation_attempts", 1)

    investigation = run_investigation_agent(
        claim=state["claim"],
        attempt=attempt,
        previous_summary=state.get("previous_summary", ""),
    )

    return {
        "retrieved_evidence": investigation["retrieved_evidence"],
        "investigation_notes": [
            investigation["investigation_summary"]
        ],
        "investigation_summary": investigation["investigation_summary"],
        "tool_calls": investigation["tool_calls"],
        "status": investigation["status"],
    }




def build_investigation_graph():
    graph = StateGraph(InvestigationState)

    graph.add_node("extract_facts", extract_claim_facts)
    graph.add_node("retrieve_evidence", retrieve_evidence)

    graph.set_entry_point("extract_facts")
    graph.add_edge("extract_facts", "retrieve_evidence")
    graph.add_edge("retrieve_evidence", END)

    return graph.compile()


investigation_graph = build_investigation_graph()
