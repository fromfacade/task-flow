from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
  email: EmailStr
  password: str = Field(min_length=8, max_length=128)

class UserResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: int
  email: EmailStr
  is_verified: bool
  created_at: datetime

class TokenResponse(BaseModel):
  access_token: str
  token_type: str

class JobCreate(BaseModel):
  job_type: str = Field(
    min_length=1,
    max_length=100,
  )

  payload: dict[str, Any]

class JobResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id:int
  user_id:int
  job_type:str
  status:str
  payload:dict[str, Any]
  result:dict[str, Any] | None
  error:str | None
  attempts:int
  created_at:datetime
  started_at:datetime | None
  completed_at:datetime | None