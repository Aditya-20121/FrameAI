"""
Celery task: fal.ai FLUX.1 Kontext try-on generation.

Counter increments only on success — a failed or retried task never costs
the user a generation slot.
"""
import asyncio
import logging

from celery_app import celery_app
from db import client as db
from services import generation as gen_svc

log = logging.getLogger(__name__)


@celery_app.task(
    name="tasks.generate.generate_try_on",
    bind=True,
    max_retries=2,
    default_retry_delay=10,
    ignore_result=True,
)
def generate_try_on(
    self,
    task_id: str,
    job_id: str,
    frame_id: str,
    session_token: str,
) -> None:
    """
    Run fal.ai FLUX.1 Kontext generation for one frame + user photo pair.
    Writes status updates to generation_tasks table throughout.
    Increments session generation counter only on successful completion.
    """
    db.update_generation_task(task_id, status="processing")

    try:
        frame = db.get_frame(frame_id)
        if not frame:
            log.error("Frame %s not found — cannot generate for task %s", frame_id, task_id)
            db.update_generation_task(task_id, status="failed")
            return

        r2_key = asyncio.run(gen_svc.generate_try_on(job_id, frame, task_id))
        db.update_generation_task(task_id, status="complete", image_r2_key=r2_key)
        db.increment_generations(session_token)

    except Exception as exc:
        log.exception("Generation failed for task %s", task_id)
        db.update_generation_task(task_id, status="failed")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
