
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = PROJECT_ROOT / "docs"
VECTOR_STORE_DIR = PROJECT_ROOT / "vector_store"

SOURCE_FILES = [
    "DGCA_CAR_Rev4.pdf",
    "Air_India_Conditions_of_Carriage.pdf",
]

COLLECTION_NAME = "passenger_claim_corpus"


def load_source_documents():
    documents = []

    for filename in SOURCE_FILES:
        pdf_path = CORPUS_DIR / filename

        if not pdf_path.exists():
            raise FileNotFoundError(f"Missing source document: {pdf_path}")

        loader = PyPDFLoader(str(pdf_path))
        pages = loader.load()

        for page in pages:
            page.metadata["source_file"] = filename
            page.metadata["document_type"] = (
                "dgca_regulation"
                if filename.startswith("DGCA")
                else "airline_conditions_of_carriage"
            )

        documents.extend(pages)
        print(f"Loaded {len(pages)} pages from {filename}")

    return documents


def build_index():
    documents = load_source_documents()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(VECTOR_STORE_DIR),
    )

    vector_store.add_documents(chunks)

    print(f"\nIndexing complete.")
    print(f"Source pages: {len(documents)}")
    print(f"Searchable chunks added: {len(chunks)}")
    print(f"Vector store: {VECTOR_STORE_DIR}")


if __name__ == "__main__":
    build_index()
