
from typing import Literal

from langchain_core.tools import tool

from services.retrieval.retriever import retrieve_claim_evidence


@tool
def search_claim_corpus(
    query: str,
    document_type: Literal[
        "dgca_regulation",
        "airline_conditions_of_carriage",
    ] | None = None,
) -> list[dict]:
    """Search the indexed DGCA regulations and airline conditions for relevant evidence."""
    return retrieve_claim_evidence(
        query=query,
        k=5,
        document_type=document_type,
    )



@tool
def lookup_clause_by_id(
    clause_id: str,
    document_type: Literal[
        "dgca_regulation",
        "airline_conditions_of_carriage",
    ] = "dgca_regulation",
) -> list[dict]:
    """Retrieve corpus chunks containing an exact clause reference."""
    from services.retrieval.retriever import _vector_store

    results = _vector_store.get(
        where={"document_type": {"$eq": document_type}},
        where_document={"$contains": clause_id},
        include=["documents", "metadatas"],
    )

    evidence = []

    for content, metadata in zip(
        results["documents"],
        results["metadatas"],
    ):
        evidence.append({
            "content": content,
            "source_file": metadata.get("source_file"),
            "document_type": metadata.get("document_type"),
            "page": metadata.get("page"),
        })

    return evidence



@tool
def lookup_claim_field(
    claim: dict,
    field_path: str,
) -> dict:
    """Read a specific field from the submitted claim using a dotted path."""
    if not field_path or not field_path.strip():
        return {"found": False, "reason": "Field path cannot be empty."}

    value = claim

    for key in field_path.split("."):
        if not isinstance(value, dict) or key not in value:
            return {
                "found": False,
                "field_path": field_path,
                "reason": "Field does not exist in the submitted claim.",
            }

        value = value[key]

    return {
        "found": True,
        "field_path": field_path,
        "value": value,
    }


CLAIM_INVESTIGATION_TOOLS = [
    search_claim_corpus,
    lookup_clause_by_id,
    lookup_claim_field,
]
