
from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VECTOR_STORE_DIR = PROJECT_ROOT / "vector_store"

COLLECTION_NAME = "passenger_claim_corpus"

_embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

_vector_store = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=_embeddings,
    persist_directory=str(VECTOR_STORE_DIR),
)


def retrieve_claim_evidence(
    query: str,
    k: int = 5,
    document_type: str | None = None,
) -> list[dict]:
    """Retrieve relevant evidence from the indexed claim corpus."""

    filters = (
        {"document_type": document_type}
        if document_type
        else None
    )

    results = _vector_store.similarity_search_with_score(
        query,
        k=k,
        filter=filters,
    )

    evidence = []

    for document, score in results:
        evidence.append(
            {
                "content": document.page_content,
                "source_file": document.metadata.get("source_file"),
                "document_type": document.metadata.get("document_type"),
                "page": document.metadata.get("page"),
                "relevance_score": float(score),
            }
        )

    return evidence
