import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

load_dotenv()

password_hasher = PasswordHash.recommended()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
  os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)

if not SECRET_KEY:
  raise RuntimeError("SECRET_KEY isn't configured in the .env file...")

def hash_password(password: str) -> str:
  return password_hasher.hash(password)

def verify_password(
    plain_password: str,
    stored_password_hash: str,
) -> bool:
  return password_hasher.verify(
    plain_password,
    stored_password_hash,
  )

def create_access_token(subject: str) -> str:
  expires_at = datetime.now(timezone.utc) + timedelta(
    minutes=ACCESS_TOKEN_EXPIRE_MINUTES
  )

  payload = {
    "sub": subject,
    "exp": expires_at,
  }

  return jwt.encode(
    payload,
    SECRET_KEY,
    algorithm=ALGORITHM,
  )

def decode_access_token(token:str) -> str:
  payload = jwt.decode(
    token,
    SECRET_KEY,
    algorithms=[ALGORITHM],
  )

  subject = payload.get("sub")

  if not isinstance(subject, str):
    raise InvalidTokenError("Token does not contain a valid subject")

  return subject