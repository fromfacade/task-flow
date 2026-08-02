import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
  raise RuntimeError("DATABASE_URL was not found in the .env file")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
  bind=engine,
  autoflush=False,
  autocommit=False,
)

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()