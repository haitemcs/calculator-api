# FastAPI Async Task Processing Platform

A FastAPI port of the architecture in [django-async-task-platform](https://github.com/haitemcs/django-async-task-platform). PostgreSQL stores task records, Redis brokers jobs, and Celery workers process them asynchronously.

## Architecture

    Client -> FastAPI -> PostgreSQL (task record)
                     -> Redis broker -> Celery worker -> PostgreSQL (result/status)

Stack: FastAPI, SQLAlchemy, PostgreSQL, Redis, Celery, JWT, Argon2 password hashing, Alembic, Docker Compose, pytest, Ruff, and GitHub Actions.

## Run with Docker

    cp .env.example .env
    # Change SECRET_KEY and database credentials before exposing the service.
    docker compose up --build -d

Open http://localhost:8000/docs.

    docker compose ps
    docker compose logs --tail=100 web celery_worker db redis
    docker compose exec web alembic current
    docker compose down

Named volumes preserve data after docker compose down. Avoid docker compose down -v unless you intend to delete it.

## Run locally

Create a virtual environment, install requirements, copy .env.example to .env, and run PostgreSQL and Redis. Then:

    alembic upgrade head
    uvicorn app.main:app --reload
    celery -A app.worker.celery_app worker --loglevel=INFO

On Windows, use Celery's --pool=solo option if the default worker pool is problematic.

## API

All application endpoints use /api/v1. Interactive docs are at /docs.

### Authentication
- POST /api/v1/auth/register — create an account with JSON email/password
- POST /api/v1/auth/token — obtain a JWT using form fields username (your email) and password
- GET /api/v1/auth/me — current authenticated user

Registration body:

    {"email":"user@example.com","password":"use-a-long-password"}

In Swagger UI, use the Authorize dialog and enter the email as username and the password. Alternatively, POST form-encoded username and password to /api/v1/auth/token.

### Background tasks
- POST /api/v1/tasks — submit task (202 Accepted)
- GET /api/v1/tasks — list your tasks; supports status, limit (1–100), offset
- GET /api/v1/tasks/{task_id} — retrieve status/result
- PATCH /api/v1/tasks/{task_id} — rename a completed task
- DELETE /api/v1/tasks/{task_id} — delete your task

Example request:

    {
      "name": "multiply two values",
      "operation": "calculate",
      "input_data": {"operation": "multiply", "a": 6, "b": 7}
    }

Supported input_data payloads:

    {"operation":"add","a":2,"b":3}
    {"operation":"subtract","a":7,"b":4}
    {"operation":"multiply","a":6,"b":7}
    {"operation":"divide","a":8,"b":2}
    {"operation":"sum","numbers":[1,2,3]}

Poll the task detail endpoint to observe pending, running, success, or failure. Invalid inputs and division by zero are represented as failed tasks. User expressions are never passed to eval.

### Health checks
- GET /health/live — process liveness
- GET /health/ready — PostgreSQL and Redis connectivity without raw exception details

Readiness does not guarantee a worker is consuming jobs.

## Reliability notes

The task row is committed before Celery dispatch. If broker dispatch fails, the row is retained and marked failed for visibility. Celery uses late acknowledgements, low prefetch, and retry/backoff settings. Exactly-once processing is not guaranteed: worker or broker failures may require reconciliation. This baseline does not yet implement the reference project's Redis idempotency middleware or durable transactional outbox; these remain explicit hardening tasks, not implied guarantees.

## Layout

    app/api.py           # Auth and task endpoints
    app/config.py        # Environment settings
    app/database.py      # SQLAlchemy engine/session
    app/main.py          # FastAPI app and health checks
    app/models.py        # User and task ORM models
    app/schemas.py       # Pydantic contracts
    app/security.py      # JWT and password hashing
    app/tasks.py         # Celery worker and calculator workload
    app/worker.py        # Celery entry point
    migrations/          # Alembic migration history
    tests/               # Unit tests

## Checks

    ruff check --select F app tests migrations
    pytest -q
    alembic upgrade head

Reference implementation: [haitemcs/django-async-task-platform](https://github.com/haitemcs/django-async-task-platform). This is an idiomatic FastAPI/SQLAlchemy translation of the core architecture, not a line-for-line Django port.
