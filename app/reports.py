from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Report
from .schemas import ReportCreate
from .auth import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- ADD REPORT ----------------

@router.post("/")
def add_report(
    report: ReportCreate,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_report = Report(
        patient_id=report.patient_id,
        report_type=report.report_type,
        content=report.content
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report

# ---------------- GET REPORTS BY PATIENT ----------------

@router.get("/{patient_id}")
def get_reports(
    patient_id: str,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reports = db.query(Report).filter(Report.patient_id == patient_id).all()
    return reports
