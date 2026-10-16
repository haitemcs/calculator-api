import enum, uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
def utcnow(): return datetime.now(timezone.utc)
class TaskStatus(str, enum.Enum):
    PENDING="pending"; RUNNING="running"; SUCCESS="success"; FAILURE="failure"; RETRY="retry"
class User(Base):
    __tablename__="users"
    id: Mapped[int]=mapped_column(primary_key=True)
    email: Mapped[str]=mapped_column(String(255),unique=True,index=True)
    hashed_password: Mapped[str]=mapped_column(String(255))
    is_active: Mapped[bool]=mapped_column(Boolean,default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
    tasks: Mapped[list["Task"]]=relationship(back_populates="owner",cascade="all, delete-orphan")
class Task(Base):
    __tablename__="tasks"
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
    owner_id: Mapped[int]=mapped_column(ForeignKey("users.id",ondelete="CASCADE"),index=True)
    name: Mapped[str]=mapped_column(String(160),default="Background task")
    operation: Mapped[str]=mapped_column(String(40),default="calculate")
    input_data: Mapped[dict]=mapped_column(JSON)
    result_data: Mapped[dict|None]=mapped_column(JSON,nullable=True)
    status: Mapped[TaskStatus]=mapped_column(Enum(TaskStatus),default=TaskStatus.PENDING,index=True)
    error_message: Mapped[str|None]=mapped_column(Text,nullable=True)
    retry_count: Mapped[int]=mapped_column(Integer,default=0)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow,index=True)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow,onupdate=utcnow)
    started_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    finished_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    owner: Mapped[User]=relationship(back_populates="tasks")
