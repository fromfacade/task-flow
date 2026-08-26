import logging
import time
import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from .database import SessionLocal
from .models import Job

WORKER_ID = os.getpid()
POLL_INTERVAL_SECONDS = 2
RETRY_DELAY_SECONDS = 3
MAX_ATTEMPTS = 3

logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

def process_job(
    job_type: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
  if job_type == "test":
    logger.info("Processing test job...")

    # simulates some work taking time
    time.sleep(2)

    return {
      "processed": True,
      "message": payload.get("message"),
    }
  raise ValueError(
    f"Unsupported job type: {job_type}"
  )

def claim_next_job():

  with SessionLocal() as db:
    job = db.scalar(
      select(Job)
      .where(Job.status == "queued")
      .order_by(Job.created_at.asc())
      .with_for_update(skip_locked=True)
      .limit(1)
    )

    if job is None:
      return None

    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    job.attempts += 1

    job_id = job.id
    job_type = job.job_type
    payload = dict(job.payload)

    db.commit()

    logger.info(
      "Worker %s claimed job %s (%s)",
      WORKER_ID,
      job_id,
      job_type,
    )

    return job_id, job_type, payload

def complete_job(
    job_id: int,
    result: dict[str, Any],
):
  with SessionLocal() as db:
    job = db.get(Job, job_id)

    if job is None:
      logger.error(
        "Job %s disappeared before completion.",
        job_id,
      )

      return

    job.status = "completed"
    job.result = result
    job.error = None
    job.completed_at = datetime.now(timezone.utc)

    db.commit()

    logger.info(
      "Completed job %s",
      job_id,
    )

def fail_job(
    job_id: int,
    error: Exception,
) -> bool:
  """
  records a job failue. 
  returns true if job is retired.
  returns false if job permanantly failed.
  """

  with SessionLocal() as db:
    job = db.get(Job, job_id)

    if job is None:
      logger.error(
        "Job %s disappeared after failure.",
        job_id,
      )
      return

    job.error = str(error)

    if job.attempts < MAX_ATTEMPTS:
      job.status = "queued"
      job.started_at = None
      job.completed_at = None

      db.commit()

      logger.warning(
        "Job %s failed on attempt %s%s. Retrying...",
        job_id,
        job.attempts,
        MAX_ATTEMPTS,
      )

      return True

    job.status = "failed"
    job.completed_at = datetime.now(timezone.utc)

    db.commit()

    logger.error(
      "Job %s permanently failed after %s attempts: %s",
      job_id,
      job.attempts,
      error,
    )

    return False

def run_worker():
  logger.info(
    "Taskflow worker %s started.",
    WORKER_ID,
  )

  while True:
    claimed_job = claim_next_job()

    if claimed_job is None:
      time.sleep(POLL_INTERVAL_SECONDS)
      continue

    job_id, job_type, payload = claimed_job

    try:
      result = process_job(
        job_type,
        payload,
      )

      complete_job(
        job_id,
        result,
      )

    except Exception as error:
      will_retry = fail_job(
        job_id,
        error,
      )

      if will_retry:
        time.sleep(RETRY_DELAY_SECONDS)

if __name__ == "__main__":
  try:
    run_worker()

  except KeyboardInterrupt:
    logger.info("TaskFlow worker stopped.")