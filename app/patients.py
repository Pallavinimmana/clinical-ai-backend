from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import uuid

from .database import SessionLocal
from .auth import get_current_user

router = APIRouter(prefix="/patients")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Temporary in-memory storage (we’ll move to DB next)
patients = []

@router.post("/")
def add_patient(
    name: str,
    age: int,
    gender: str,
    user: str = Depends(get_current_user)
):
    patient = {
        "id": str(uuid.uuid4()),
        "name": name,
        "age": age,
        "gender": gender,
        "created_by": user
    }
    patients.append(patient)
    return patient

@router.get("/")
def list_patients(user: str = Depends(get_current_user)):
    return patients
