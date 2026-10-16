"""Pydantic schemas for request validation and API responses.

Database models describe stored rows; these schemas define the fields clients
can send and receive. Keeping the two separate prevents leaking internal fields.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import TaskStatus


class UserCreate(BaseModel):
    """Input required to register an account."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    """Public account fields; never include the password hash here."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    """Response returned after login."""

    access_token: str
    token_type: str = "bearer"


class TaskCreate(BaseModel):
    """Input for creating a background task."""

    name: str = Field(default="Background task", min_length=1, max_length=160)
    operation: str = Field(default="calculate", min_length=1, max_length=40)
    input_data: dict


class TaskUpdate(BaseModel):
    """Fields clients are allowed to edit on an existing task."""

    name: str | None = Field(default=None, min_length=1, max_length=160)


class TaskRead(BaseModel):
    """Fields returned when the API sends a task to the client."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    operation: str
    input_data: dict
    result_data: dict | None
    status: TaskStatus
    error_message: str | None
    retry_count: int
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class TaskPage(BaseModel):
    """A page of task results and the information needed to request another page."""

    items: list[TaskRead]
    total: int
    limit: int
    offset: int
