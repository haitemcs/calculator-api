"""Celery setup and the calculator task executed in the background."""
from datetime import datetime, timezone

from celery import Celery
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import Task, TaskStatus

# Redis is the queue broker. The task's business result is saved in PostgreSQL.
celery_app = Celery(
    "async_task_platform",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# These settings improve worker recovery and limit how many jobs are reserved
# at once. They do not guarantee exactly-once execution.
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_track_started=True,
)


def calculate(data: dict) -> dict:
    """Perform one supported arithmetic operation without evaluating code."""
    operation = data.get("operation")

    if operation == "sum":
        values = data.get("numbers")
        # bool is also an int in Python, so reject True and False explicitly.
        if (
            not isinstance(values, list)
            or not values
            or not all(
                isinstance(value, (int, float)) and not isinstance(value, bool)
                for value in values
            )
        ):
            raise ValueError("numbers must be a non-empty list of numbers")
        return {"operation": operation, "result": sum(values)}

    a, b = data.get("a"), data.get("b")
    if operation not in {"add", "subtract", "multiply", "divide"}:
        raise ValueError("Unsupported operation")
    if not all(
        isinstance(value, (int, float)) and not isinstance(value, bool)
        for value in (a, b)
    ):
        raise ValueError("a and b must be numbers")

    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    else:
        if b == 0:
            raise ValueError("division by zero")
        result = a / b

    return {"operation": operation, "a": a, "b": b, "result": result}


@celery_app.task(
    bind=True,
    name="app.tasks.process_task",
    autoretry_for=(ConnectionError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def process_task(self, task_id: str) -> dict:
    """Load a task from PostgreSQL, execute it, and save the new state."""
    # A worker is a separate process, so it needs its own database session.
    db: Session = SessionLocal()

    try:
        task = db.get(Task, task_id)
        if task is None:
            # The task might have been deleted before the worker received the job.
            return {"status": "missing", "task_id": task_id}

        # Commit the running state before doing the calculation so API clients
        # can see that a worker has picked up the task.
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(timezone.utc)
        task.retry_count = self.request.retries
        task.error_message = None
        db.commit()

        try:
            if task.operation != "calculate":
                raise ValueError("Unsupported task type")
            result = calculate(task.input_data)
        except (ValueError, TypeError) as exc:
            # Invalid input is recorded as a failed job, not retried indefinitely.
            task.status = TaskStatus.FAILURE
            task.error_message = str(exc)[:2000]
            task.finished_at = datetime.now(timezone.utc)
            db.commit()
            return {"task_id": task_id, "status": "failure"}

        # Save the result in the same row that the API uses to show task status.
        task.result_data = result
        task.status = TaskStatus.SUCCESS
        task.finished_at = datetime.now(timezone.utc)
        db.commit()
        return {"task_id": task_id, "status": "success", "result": result}

    except Exception:
        # Roll back uncommitted database changes before passing the error onward.
        db.rollback()
        raise
    finally:
        # Always release the connection, even if processing raised an exception.
        db.close()
