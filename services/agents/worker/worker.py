import time
from unittest import result
from uuid import UUID

from arq.connections import RedisSettings

from common.db.session import SessionLocal, settings
from common.db.models import ClaimRecord, ProcessingRun
from services.agents.graphs.claim_workflow import claim_workflow



async def process_claim(ctx, run_id: str):
    with SessionLocal() as db:
        run = db.get(ProcessingRun, UUID(run_id))

        if run is None:
            return {"status": "not_found", "run_id": run_id}

        claim_record = db.get(ClaimRecord, run.claim_id)

        if claim_record is None:
            run.status = "failed"
            db.commit()
            return {"status": "failed", "reason": "Claim not found"}

        run.status = "processing"
        db.commit()

        initial_state = {
            "claim": claim_record.payload,
            "disruption_type": "unspecified",
            "notice_hours": None,
            "alternate_accepted": False,
            "investigation_notes": [],
            "retrieved_evidence": [],
            "status": "started",
            "assessment": {},
            "verified_result": {},
            "investigation_attempts": 0,
}

        processing_start = time.perf_counter()

        result = claim_workflow.invoke(initial_state)

        processing_time = time.perf_counter() - processing_start

        result["processing_time_seconds"] = round(processing_time, 3)

        run.result = result
        run.status = "completed"
        db.commit()

        return {
            "status": "completed",
            "run_id": run_id,
        }


class WorkerSettings:
    functions = [process_claim]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 5
    job_timeout = 300
