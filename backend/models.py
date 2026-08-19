from datetime import datetime
from typing import Any

from sqlalchemy import (
  Boolean,
  DateTime,
  ForeignKey,
  Integer,
  JSON,
  String,
  Text,
  func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

class User(Base):
  __tablename__ = "users"

  id: Mapped[int] = mapped_column(
    Integer,
    primary_key=True,
    index=True,
  )

  email: Mapped[str] = mapped_column(
    String(255),
    unique=True,
    nullable=True,
    index=True,
  )

  password_hash: Mapped[str] = mapped_column(
    String(255),
    nullable=False,
  )

  is_verified: Mapped[bool] = mapped_column(
    Boolean,
    default=False,
    nullable=False,
  )

  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
    nullable=True,
  )

  jobs: Mapped[list["Job"]] = relationship(
    back_populates="owner",
    cascade="all, delete-orphan",
  )

class Job(Base):
  __tablename__ = "jobs"

  id: Mapped[int] = mapped_column(
    Integer,
    primary_key=True,
    index=True
  )

  user_id: Mapped[int] = mapped_column(
    ForeignKey("users.id"),
    nullable=False,
    index=True,
  )

  job_type: Mapped[str] = mapped_column(
    String(100),
    nullable=False,
  )

  status: Mapped[str] = mapped_column(
    String(20),
    default="queued",
    nullable=False,
    index=True,
  )

  payload: Mapped[dict[str, Any]] = mapped_column(
    JSON,
    nullable=False,
  )

  result: Mapped[dict[str, Any] | None] = mapped_column(
      JSON,
      nullable=True,
  )

  error: Mapped[str | None] = mapped_column(
    Text,
    nullable=True,
  )

  attempts: Mapped[int] = mapped_column(
    Integer,
    default=0,
    nullable=False,
  )

  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
    nullable=True,
  )

  started_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True),
    nullable=True,
  )

  completed_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True),
    nullable=True,
  )

  owner: Mapped["User"] = relationship(
    back_populates="jobs"
  )