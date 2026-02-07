from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Report, LabResult, Alert, ClinicalNote
from .auth import get_current_user
from .gemini_service import generate_medical_insight

router = APIRouter(prefix="/analysis", tags=["AI Analysis"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/{patient_id}")
def analyze_patient(
    patient_id: str,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reports = db.query(Report).filter(Report.patient_id == patient_id).all()
    labs = db.query(LabResult).filter(LabResult.patient_id == patient_id).all()
    notes = db.query(ClinicalNote).filter(
        ClinicalNote.patient_id == patient_id
    ).all()

    if not reports and not labs and not notes:
        return [{
            "severity": "INFO",
            "message": "No data found for this patient."
        }]

    radiology_text = " ".join(
        (r.content or "").lower()
        for r in reports
        if r.report_type.lower() in ["radiology", "ct", "mri", "xray", "echo"]
    )

    clinical_text = " ".join(
        (n.content or "").lower() for n in notes
    )

    crp = None
    wbc = None

    for lab in labs:
        if lab.test_name:
            if lab.test_name.upper() == "CRP":
                crp = lab.value
            elif lab.test_name.upper() == "WBC":
                wbc = lab.value

    infection_negative = any(
        phrase in radiology_text
        for phrase in [
            "no infection",
            "no evidence of infection",
            "no signs of infection",
            "no acute infection",
        ]
    )

    severity = None
    base_message = ""

    if infection_negative and (
        (crp and crp > 100) or (wbc and wbc > 15000)
    ):
        severity = "HIGH"
        base_message = "Radiology reports no infection, but inflammatory markers are critically elevated."

    elif infection_negative and (
        (crp and 50 <= crp <= 100) or (wbc and 11000 <= wbc <= 15000)
    ):
        severity = "MEDIUM"
        base_message = "Radiology reports no infection, but inflammatory markers are moderately elevated."

    elif crp is not None or wbc is not None:
        severity = "LOW"
        base_message = "Radiology, labs, and clinical notes show no major discrepancy."

    if not severity:
        return [{
            "severity": "INFO",
            "message": "No clinically significant discrepancy detected."
        }]

    labs_summary = []
    if crp is not None:
        labs_summary.append(f"CRP: {crp} mg/L")
    if wbc is not None:
        labs_summary.append(f"WBC: {wbc} cells/mm3")

    ai_explanation = generate_medical_insight(
        radiology_text=radiology_text or "No radiology findings.",
        labs_summary=", ".join(labs_summary) or "No abnormal labs.",
        clinical_notes=clinical_text
    )

    alert = Alert(
        patient_id=patient_id,
        severity=severity,
        message=f"{base_message} {ai_explanation}"
    )

    db.add(alert)
    db.commit()

    return [{
        "patient_id": patient_id,
        "severity": severity,
        "message": alert.message
    }]
