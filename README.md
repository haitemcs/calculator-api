# FastAPI Async Task Platform

A background-task API built with FastAPI, PostgreSQL, Redis, and Celery. It is a learning project based on the same general idea as my [Django async task project](https://github.com/haitemcs/django-async-task-platform), implemented with a different Python web framework.

## Follow one task through the code

When you submit a task, the API saves it in PostgreSQL and sends its ID to Redis through Celery. A separate Celery worker reads the ID, loads the task from PostgreSQL, runs the calculation, and saves the result. The API can respond before the calculation finishes.

```text
Client -> FastAPI -> PostgreSQL (save task)
                 -> Redis queue -> Celery worker -> PostgreSQL (save result)
```

## Suggested reading order

Open these files in order. Each step builds on the previous one.

1. `app/main.py` — where the FastAPI app is created and the routes are registered.
2. `app/api.py` — the HTTP endpoints and the flow from request to database.
3. `app/schemas.py` — the shapes of incoming requests and outgoing responses.
4. `app/models.py` — the Python classes that represent database tables.
5. `app/database.py` — database connections and sessions.
6. `app/security.py` — password hashing, JWT creation, and token validation.
7. `app/tasks.py` — the calculator and the work done by the background worker.
8. `app/worker.py` — the module Celery imports when starting a worker.
9. `app/config.py` — settings shared by the rest of the application.
10. `migrations/` — versioned changes to the database schema.
11. `tests/` — automated checks.

A good first exercise: start at `create_task()` in `app/api.py`, then follow the task ID into `process_task()` in `app/tasks.py`.

## Run with Docker

Copy the example environment file and review its values:

```bash
cp .env.example .env
docker compose up --build -d
```

Set your own random `SECRET_KEY` and appropriate database credentials in `.env` before using the service beyond local development.

Open [http://localhost:8000/docs](http://localhost:8000/docs) to try the API. Useful commands:

```bash
docker compose ps
docker compose logs --tail=100 web celery_worker db redis
docker compose exec web alembic current
docker compose down
```

Docker volumes keep database data when you run `docker compose down`. Don't use `docker compose down -v` unless you intend to remove the volumes and their data.

## Run locally

You'll need Python, PostgreSQL, and Redis. Create a virtual environment, install the packages from `requirements.txt`, copy `.env.example` to `.env`, and start the database and Redis. Then run the migration and API:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

In a separate terminal, start the worker:

```bash
celery -A app.worker.celery_app worker --loglevel=INFO
```

On Windows, try adding `--pool=solo` if Celery's default worker pool causes problems.

## Endpoints

The API routes use the `/api/v1` prefix. Swagger UI is available at `/docs`.

### Authentication

- `POST /api/v1/auth/register` — create an account with JSON email and password.
- `POST /api/v1/auth/token` — log in and receive a JWT. Send form fields named `username` (your email) and `password`.
- `GET /api/v1/auth/me` — return the currently authenticated user.

Example registration body:

```json
{"email": "user@example.com", "password": "use-a-long-password"}
```

In Swagger UI, use **Authorize** and enter your email as the username.

### Background tasks

- `POST /api/v1/tasks` — submit a task; returns `202 Accepted` when queued.
- `GET /api/v1/tasks` — list your tasks; supports `status`, `limit` (1–100), and `offset`.
- `GET /api/v1/tasks/{task_id}` — check a task's status, result, or error.
- `PATCH /api/v1/tasks/{task_id}` — rename a task that is no longer pending or running.
- `DELETE /api/v1/tasks/{task_id}` — delete one of your tasks.

Example task body:

```json
{
  "name": "multiply two values",
  "operation": "calculate",
  "input_data": {"operation": "multiply", "a": 6, "b": 7}
}
```

Supported calculator operations are `add`, `subtract`, `multiply`, `divide`, and `sum`. Invalid inputs and division by zero are stored as failed tasks.

### Health checks

- `GET /health/live` — confirms the API process responds.
- `GET /health/ready` — checks PostgreSQL and Redis connectivity.

Readiness does not prove that a Celery worker is running.

## Checks

Run these from the repository root:

```bash
ruff check --select F app tests migrations
pytest -q
alembic upgrade head
```

Run these checks in your own environment before relying on a change; I have not independently verified the live Docker and Celery setup in this session.

## Reliability notes

The task row is committed before Celery dispatch. If the broker cannot accept the job, the row is kept and marked as failed. Celery's acknowledgement and retry settings help with recovery, but do not guarantee exactly-once execution.

This version does not include a durable transactional outbox, Redis idempotency middleware, or automatic reconciliation for tasks left unfinished after a crash. Those are useful future improvements.

## Project layout

```text
app/
  api.py       # HTTP endpoints
  config.py    # environment-based settings
  database.py  # SQLAlchemy engine and sessions
  main.py      # FastAPI application and health checks
  models.py    # database tables and relationships
  schemas.py   # request and response validation
  security.py  # password hashing and JWT authentication
  tasks.py     # calculator and Celery task
  worker.py    # Celery entry point
migrations/    # Alembic schema history
tests/         # automated checks
.github/       # GitHub Actions workflow
```
