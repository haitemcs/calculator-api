"""SQLAlchemy models: the Python classes that map to database tables."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    """Create a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class TaskStatus(str, enum.Enum):
    """Possible states for a background task."""

    PENDING = "pending"  # Waiting for a worker.
    RUNNING = "running"  # A worker is processing it.
    SUCCESS = "success"  # Finished successfully.
    FAILURE = "failure"  # Input or processing failed.
    RETRY = "retry"  # Reserved for retry-state reporting.


class User(Base):
    """A registered account that owns tasks."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # One user can own many tasks. The relationship connects both model classes.
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )


class Task(Base):
    """Stored input, status, and result for one background job."""

    __tablename__ = "tasks"

    # Each task receives a UUID string as its primary key.
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(160), default="Background task")
    operation: Mapped[str] = mapped_column(String(40), default="calculate")

    # JSON keeps inputs and results as structured data.
    input_data: Mapped[dict] = mapped_column(JSON)
    result_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.PENDING, index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    # These timestamps help track queue time and processing duration.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # The reverse side of User.tasks.
    owner: Mapped[User] = relationship(back_populates="tasks")
