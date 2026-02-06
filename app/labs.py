from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import LabResult
from .schemas import LabCreate
from .auth import get_current_user

router = APIRouter(prefix="/labs", tags=["Lab Results"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- ADD LAB RESULT ----------------

@router.post("/")
def add_lab(
    lab: LabCreate,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_lab = LabResult(
        patient_id=lab.patient_id,
        test_name=lab.test_name,
        value=lab.value,
        unit=lab.unit
    )
    db.add(new_lab)
    db.commit()
    db.refresh(new_lab)
    return new_lab

# ---------------- GET LAB RESULTS ----------------

@router.get("/{patient_id}")
def get_labs(
    patient_id: str,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    labs = db.query(LabResult).filter(LabResult.patient_id == patient_id).all()
    return labs
