from fastapi import FastAPI

from . import models
from .database import engine

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

