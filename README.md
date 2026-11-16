
# Air Passenger Claim Triage Service

A multi-agent AI-powered air passenger compensation claim triage service using DGCA regulations and airline Conditions of Carriage.

## 1. Project Overview

The Air Passenger Claim Triage Service is an academic AI decision-support system that investigates passenger claims arising from flight disruptions such as cancellations, delays and denied boarding.

The system validates claim information, retrieves relevant regulatory provisions using semantic search, investigates supporting evidence and produces entitlement recommendations with clause citations.

The workflow uses an LLM-powered Investigation Agent alongside deterministic entitlement assessment and citation verification.

**The system provides decision support only. It does not authorize or process compensation payments.**

## 2. Objectives

- Validate passenger claim information and enforce data integrity.
- Investigate flight disruption details.
- Retrieve relevant DGCA regulations and airline provisions.
- Generate evidence-grounded investigation summaries.
- Assess separate entitlement categories.
- Verify supporting clause citations.
- Escalate cases when sufficient evidence is unavailable.
- Support asynchronous claim processing and application monitoring.

## 3. Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| Backend API | FastAPI |
| Agent orchestration | LangGraph |
| LLM | Google Gemini 3.5 Flash Lite |
| LLM framework | LangChain |
| Embedding model | Sentence Transformers – all-MiniLM-L6-v2 |
| Vector database | ChromaDB |
| Relational database | PostgreSQL |
| Background processing | Redis and ARQ |
| Data validation | Pydantic |
| Frontend | HTML, CSS, JavaScript |
| Monitoring | Prometheus Client |
| Containerization | Docker Compose |
| Testing | Pytest |

## 4. System Workflow

1. **Claim Submission:** Passenger submits flight, passenger and disruption details through the web interface.
2. **Validation:** FastAPI and Pydantic validate the request and enforce business rules.
3. **Background Processing:** The claim is stored in PostgreSQL and queued through Redis and ARQ.
4. **Investigation:** The LangGraph workflow invokes the Investigation Agent, which uses retrieval tools to identify relevant provisions.
5. **Evidence Retrieval:** ChromaDB retrieves relevant passages from indexed regulatory documents using semantic embeddings.
6. **Entitlement Assessment:** Deterministic Python logic evaluates the supported entitlement categories.
7. **Verification:** Retrieved evidence is checked against cited provisions. Unsupported recommendations are escalated.
8. **Results:** The frontend displays the investigation summary, entitlement decisions and supporting citations.

## 5. Regulatory Sources

- DGCA Civil Aviation Requirements, Section 3, Series M, Part IV, Revision 4.
- Air India Conditions of Carriage.

## 6. Testing and Evaluation

- **25 automated tests passed** using Pytest.
- Evaluation scenarios cover claim validation, mandatory cancellation handling, missing information and invalid input.
- **6 evaluation checks passed** in the recorded evaluation run.
- The mandatory cancellation demonstration successfully produced:
  - Flight cancellation compensation: Not payable.
  - Meals and refreshments: Payable.
  - Citation verification: Verified.

## 7. Running the Project

### Prerequisites

- Python 3.12
- Docker Desktop
- Google Gemini API key

### Setup

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file using the required environment variables:

```env
DATABASE_URL=your_database_url
REDIS_URL=your_redis_url
GOOGLE_API_KEY=your_google_api_key
```

5. Start the database and Redis services:

```bash
docker compose up -d
```

6. Start the FastAPI application:

```bash
uvicorn services.api.app.main:app --reload
```

7. Start the background worker in a separate terminal:

```bash
python -m arq services.agents.worker.worker.WorkerSettings
```

8. Open the frontend at:

```text
http://127.0.0.1:8000/
```

### Running Tests

```bash
python -m pytest -q
```

## 8. Project Limitations

- The current entitlement assessment supports the implemented mandatory cancellation demonstration case rather than every possible disruption scenario.
- The system depends on the availability of the configured LLM and indexed regulatory corpus.
- Citation verification checks whether cited provisions are present in retrieved evidence; it does not establish complete legal correctness.
- The project is an academic prototype and requires further evaluation before any real-world use.

## 9. Disclaimer

This project is an academic decision-support prototype. Its recommendations are not legally binding and do not replace decisions by airlines or relevant regulatory authorities.
