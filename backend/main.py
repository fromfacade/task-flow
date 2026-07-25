from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, get_db
from .database import hash_password

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def home():
  return {
    "message": "taskflow running"
  }

@app.get("/health")
def health_check():
  return {
    "status": "healthy",
    "database": "configured",
  }

@app.post(
    "/signup",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup(
  user_data: schemas.UserCreate,
  db: Annotated[Session, Depends(get_db)],
):
  existing_user = db.scalar(
    select(models.User).where(
      models.User.email == user_data.email.lower()
    )
  )

  if existing_user:
    raise HTTPException(
      status_code=status.HTTP_409_CONFLICT,
      detail="An account with this email already exists...",
    )

  new_user = models.User(
    email=user_data.email.lower(),
    password_hash=hash_password(user_data.password)
  )

  db.add(new_user)

  try:
    db.commit()
  except IntegrityError:
    db.rollback()

    raise HTTPException(
      status_code=status.HTTP_409_CONFLICT,
      detail="An account with this email already exists...",
    )

  db.refresh(new_user)

  return new_user