from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Report, LabResult, Alert, ClinicalNote
from .auth import get_current_user
from .gemini_service import generate_medical_insight

router = APIRouter(prefix="/analysis", tags=["AI Analysis"])


# ---------------- DATABASE DEP ----------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- AI DISCREPANCY CHECK ----------------

@router.post("/{patient_id}")
def analyze_patient(
    patient_id: str,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1️⃣ Fetch all patient data
    reports = db.query(Report).filter(Report.patient_id == patient_id).all()
    labs = db.query(LabResult).filter(LabResult.patient_id == patient_id).all()
    notes = db.query(ClinicalNote).filter(
        ClinicalNote.patient_id == patient_id
    ).all()

    # 2️⃣ If absolutely nothing exists
    if not reports and not labs and not notes:
        return [{
            "severity": "INFO",
            "message": "No data found for this patient ID."
        }]

    alerts = []

    # 3️⃣ Combine radiology text (CT / MRI / X-ray / Echo)
    radiology_text = " ".join(
        (r.content or "").lower()
        for r in reports
        if r.report_type
        and r.report_type.lower() in ["radiology", "ct", "mri", "xray", "echo"]
    )

    # 4️⃣ Combine clinical notes
    clinical_text = " ".join(
        (n.content or "").lower()
        for n in notes
    )

    # 5️⃣ Extract lab values safely
    crp = None
    wbc = None

    for lab in labs:
        if lab.test_name:
            name = lab.test_name.upper()
            if name == "CRP":
                crp = lab.value
            elif name == "WBC":
                wbc = lab.value

    # 6️⃣ Detect infection-negative language
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

    # 🔴 HIGH severity
    if infection_negative and (
        (crp is not None and crp > 100) or
        (wbc is not None and wbc > 15000)
    ):
        severity = "HIGH"
        base_message = (
            "Radiology reports no infection, but inflammatory markers "
            "are critically elevated."
        )

    # 🟠 MEDIUM severity
    elif infection_negative and (
        (crp is not None and 50 <= crp <= 100) or
        (wbc is not None and 11000 <= wbc <= 15000)
    ):
        severity = "MEDIUM"
        base_message = (
            "Radiology reports no infection, but inflammatory markers "
            "are moderately elevated."
        )

    # 🟢 LOW severity
    elif (
        (crp is not None and crp < 50) or
        (wbc is not None and wbc < 11000)
    ):
        severity = "LOW"
        base_message = (
            "Radiology, laboratory results, and clinical notes "
            "show no significant discrepancy."
        )

    # 7️⃣ Generate alert + Gemini explanation
    if severity:
        labs_summary = []
        if crp is not None:
            labs_summary.append(f"CRP: {crp} mg/L")
        if wbc is not None:
            labs_summary.append(f"WBC: {wbc} cells/mm3")

        ai_explanation = generate_medical_insight(
            radiology_text=radiology_text or "No radiology findings provided.",
            labs_summary=", ".join(labs_summary) or "No lab abnormalities detected.",
            clinical_notes=clinical_text or "No clinical notes provided."
        )

        alert = Alert(
            patient_id=patient_id,
            severity=severity,
            message=f"{base_message} {ai_explanation}"
        )

        db.add(alert)
        alerts.append(alert)

    db.commit()

    # 8️⃣ Never return empty silently
    if not alerts:
        return [{
            "severity": "INFO",
            "message": "No clinically significant discrepancy detected."
        }]

    return [
        {
            "patient_id": a.patient_id,
            "severity": a.severity,
            "message": a.message
        }
        for a in alerts
    ]
