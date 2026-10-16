"""HTTP routes for accounts and background tasks."""
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task, TaskStatus, User
from app.schemas import (
    TaskCreate,
    TaskPage,
    TaskRead,
    TaskUpdate,
    Token,
    UserCreate,
    UserRead,
)
from app.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.tasks import process_task

# Version the URL prefix so a future API version can be introduced separately.
router = APIRouter(prefix="/api/v1")


@router.post("/auth/register", response_model=UserRead, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)) -> User:
    """Validate registration data and create a new account."""
    email = str(data.email).lower()

    # The database unique constraint is the final protection against duplicate
    # emails if two registration requests arrive at almost the same time.
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Account already exists")

    user = User(email=email, hashed_password=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)  # Read generated/default fields back from the database.
    return user


@router.post("/auth/token", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """Verify credentials and return a JWT access token.

    OAuth2PasswordRequestForm expects form fields called username and password.
    Here, username is the account email address.
    """
    user = db.scalar(select(User).where(User.email == form.username.lower()))
    if (
        not user
        or not verify_password(form.password, user.hashed_password)
        or not user.is_active
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Token(access_token=create_access_token(user.id))


@router.get("/auth/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)) -> User:
    """Return the account associated with the request's Bearer token."""
    return user


@router.post("/tasks", response_model=TaskRead, status_code=status.HTTP_202_ACCEPTED)
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Task:
    """Save a task and enqueue it without making the client wait for the result."""
    task = Task(
        owner_id=user.id,
        name=data.name,
        operation=data.operation,
        input_data=data.input_data,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Send only the ID to Celery; the worker reads the task details from PostgreSQL.
    try:
        process_task.delay(task.id)
    except Exception as exc:
        # Keep the row so the failed dispatch is visible when inspecting task history.
        task.status = TaskStatus.FAILURE
        task.error_message = "Task could not be queued; check broker availability."
        db.commit()
        raise HTTPException(
            status_code=503,
            detail="Background task broker unavailable",
        ) from exc

    # 202 Accepted means processing was queued, not that it has already finished.
    return task


@router.get("/tasks", response_model=TaskPage)
def list_tasks(
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskPage:
    """List this user's tasks, optionally filtered and split into pages."""
    query = select(Task).where(Task.owner_id == user.id)
    count_query = select(func.count()).select_from(Task).where(Task.owner_id == user.id)

    # Apply the same filters to the rows and total count.
    if status_filter is not None:
        query = query.where(Task.status == status_filter)
        count_query = count_query.where(Task.status == status_filter)

    items = db.scalars(
        query.order_by(Task.created_at.desc()).limit(limit).offset(offset)
    ).all()

    return TaskPage(
        items=items,
        total=db.scalar(count_query) or 0,
        limit=limit,
        offset=offset,
    )


def owned(task_id: str, db: Session, user: User) -> Task:
    """Find a task belonging to the current user or return 404.

    Using the same response for missing and other users' tasks avoids revealing
    whether another account's task ID exists.
    """
    task = db.scalar(
        select(Task).where(Task.id == task_id, Task.owner_id == user.id)
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Task:
    """Get the current user's task and its latest status/result."""
    return owned(task_id, db, user)


@router.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(
    task_id: str,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Task:
    """Rename a task once it is no longer waiting or running."""
    task = owned(task_id, db, user)

    if task.status in {TaskStatus.PENDING, TaskStatus.RUNNING}:
        raise HTTPException(
            status_code=409,
            detail="Cannot rename a task while it is running",
        )

    if data.name is not None:
        task.name = data.name

    db.commit()
    db.refresh(task)
    return task


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    """Delete a task only after confirming that it belongs to this user."""
    db.delete(owned(task_id, db, user))
    db.commit()
    return Response(status_code=204)
