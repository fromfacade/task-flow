from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, get_db
from .security import (
  hash_password,
  create_access_token,
  decode_access_token,
  verify_password
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

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

@app.post(
  "/login",
  response_model=schemas.TokenResponse,
)
def login(
  form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
  db: Annotated[Session, Depends(get_db)],
):
  #OAUTH2 calls this field "username".
  #TaskFlow uses the user's email as their username
  email = form_data.username.lower()

  user = db.scalar(
    select(models.User).where(
      models.User.email == email
    )
  )

  if user is None or not verify_password(
    form_data.password,
    user.password_hash,
  ):
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Incorrect email or password",
      headers={
        "WWW-Authenticate": "Bearer"
      },
    )

  access_token = create_access_token(
    subject=str(user.id)
  )

  return schemas.TokenResponse(
    access_token=access_token,
    token_type="bearer",
  )

def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> models.User:
  credentials_error = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={
      "WWW-Authenticate": "Bearer",
    },
  )

  try:
    user_id = int(decode_access_token(token))
  except (InvalidTokenError, ValueError):
    raise credentials_error

  user = db.get(models.User, user_id)

  if user is None:
    raise credentials_error

  return user


@app.get(
  "/users/me",
  response_model=schemas.UserResponse,
)
def read_current_user(
  current_user: Annotated[
    models.User,
    Depends(get_current_user),
  ],
):
  return current_user

@app.post(
  "/jobs",
  response_model=schemas.JobResponse,
  status_code=status.HTTP_201_CREATED,
)
def create_job(
  job_data: schemas.JobCreate,
  current_user: Annotated[
    models.User,
    Depends(get_current_user),
  ],
  db: Annotated[Session, Depends(get_db)],
):
  new_job = models.Job(
    user_id=current_user.id,
    job_type=job_data.job_type,
    payload=job_data.payload,
    status="queued",
  )

  db.add(new_job)
  db.commit()
  db.refresh(new_job)

  return new_job

@app.get(
  "/jobs",
  response_model=list[schemas.JobResponse],
)
def get_jobs(
  current_user: Annotated[
    models.User,
    Depends(get_current_user),
  ],
  db: Annotated[Session, Depends(get_db)],
):
  jobs = db.scalars(
    select(models.Job)
    .where(
      models.Job.user_id == current_user.id
    )
    .order_by(models.Job.created_at.desc())
  ).all()

  return jobs

@app.get(
  "/jobs/{job_id}",
  response_model=schemas.JobResponse,
)
def get_job(
  job_id:int,
  current_user:Annotated[
    models.User,
    Depends(get_current_user),
  ],
  db = Annotated[Session, Depends(get_db)],
):
  job = db.scalar(
    select(models.Job).where(
      models.Job.id == job_id,
      models.Job.user_id == current_user.id,
    )
  )

  if job is None:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="Job not found",
    )
  return job