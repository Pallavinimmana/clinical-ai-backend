from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Report, LabResult, Alert
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
    # 1️⃣ Fetch patient data
    reports = db.query(Report).filter(Report.patient_id == patient_id).all()
    labs = db.query(LabResult).filter(LabResult.patient_id == patient_id).all()

    # 2️⃣ Safety check
    if not reports or not labs:
        return [{
            "severity": "INFO",
            "message": (
                "Insufficient data for analysis. "
                "Please upload both radiology reports and lab results."
            )
        }]

    alerts = []

    # 3️⃣ Combine radiology text
    radiology_text = " ".join(
        (r.content or "").lower()
        for r in reports
    )

    # 4️⃣ Extract labs
    crp = None
    wbc = None

    for lab in labs:
        if lab.test_name:
            if lab.test_name.upper() == "CRP":
                crp = lab.value
            elif lab.test_name.upper() == "WBC":
                wbc = lab.value

    # 5️⃣ Detect infection-negative language
    infection_negative = any(
        phrase in radiology_text
        for phrase in [
            "no infection",
            "no evidence of infection",
            "no signs of infection",
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
            "Radiology and laboratory findings show no significant discrepancy."
        )

    # 6️⃣ Generate alert if severity detected
    if severity:
        labs_summary = []
        if crp is not None:
            labs_summary.append(f"CRP: {crp} mg/L")
        if wbc is not None:
            labs_summary.append(f"WBC: {wbc} cells/mm3")

        ai_explanation = generate_medical_insight(
            radiology_text=radiology_text,
            labs_summary=", ".join(labs_summary)
        )

        alert = Alert(
            patient_id=patient_id,
            severity=severity,
            message=f"{base_message} {ai_explanation}"
        )

        db.add(alert)
        alerts.append(alert)

    db.commit()

    # 7️⃣ JSON response
    return [
        {
            "patient_id": a.patient_id,
            "severity": a.severity,
            "message": a.message
        }
        for a in alerts
    ]
