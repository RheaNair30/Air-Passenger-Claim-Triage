
from services.retrieval.retriever import retrieve_claim_evidence


def test_retrieval_finds_cancellation_evidence():
    results = retrieve_claim_evidence(
        "Passenger accepts an alternate flight after cancellation. "
        "What compensation and assistance are applicable?",
        k=5,
    )

    assert len(results) > 0
    assert all(result["content"] for result in results)
    assert all(result["source_file"] for result in results)
