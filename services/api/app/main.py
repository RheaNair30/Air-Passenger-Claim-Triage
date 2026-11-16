
from contextlib import asynccontextmanager
from uuid import UUID, uuid4

from arq import create_pool
from fastapi import FastAPI, Request, status
from arq.connections import RedisSettings

from common.db.session import SessionLocal, settings
from common.db.models import ClaimRecord, ProcessingRun
from common.schemas.claim import ClaimInput
from fastapi import HTTPException
from pathlib import Path
from fastapi.staticfiles import StaticFiles
import time
from prometheus_client import Counter, Histogram, make_asgi_app

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis_pool = await create_pool(
        RedisSettings.from_dsn(settings.redis_url)
    )
    yield
    await app.state.redis_pool.aclose()


app = FastAPI(
    title="Air Passenger Claim Triage Service",
    description="API for submitting and validating passenger claims.",
    version="1.0.0",
    lifespan=lifespan,
)

CLAIMS_SUBMITTED = Counter(
    "claims_submitted_total",
    "Total passenger claims submitted",
)

CLAIM_PROCESSING_TIME = Histogram(
    "claim_processing_seconds",
    "Time taken to process passenger claims",
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "claim-triage-api",
    }


@app.post("/claims", status_code=status.HTTP_202_ACCEPTED)
async def submit_claim(claim: ClaimInput, request: Request):
    run_id = uuid4()
    claim_id = uuid4()
    CLAIMS_SUBMITTED.inc()

    with SessionLocal() as db:
        claim_record = ClaimRecord(
            id=claim_id,
            client_reference=claim.client_reference,
            payload=claim.model_dump(mode="json"),
        )

        processing_run = ProcessingRun(
            run_id=run_id,
            claim_id=claim_id,
            status="queued",
        )

        db.add(claim_record)
        db.add(processing_run)
        db.commit()

    await request.app.state.redis_pool.enqueue_job(
        "process_claim",
        str(run_id),
    )

    return {
        "run_id": str(run_id),
        "status": "queued",
        "message": "Claim saved and queued for processing.",
        "claim_reference": claim.client_reference,
    }
@app.get("/claims/{run_id}")
async def get_claim_status(run_id: UUID):
    with SessionLocal() as db:
        processing_run = db.get(ProcessingRun, run_id)

        if processing_run is None:
            raise HTTPException(
                status_code=404,
                detail="Processing run not found",
            )

        return {
            "run_id": str(processing_run.run_id),
            "status": processing_run.status,
            "result": processing_run.result,
        }



@app.get("/metrics")
async def metrics():
    from prometheus_client import generate_latest
    from fastapi.responses import Response

    return Response(
        generate_latest(),
        media_type="text/plain",
    )

PROJECT_ROOT = Path(__file__).resolve().parents[3]
app.mount(
    "/",
    StaticFiles(directory=PROJECT_ROOT / "app", html=True),
    name="frontend",
)