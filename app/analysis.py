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
    # 1️⃣ Fetch data
    reports = db.query(Report).filter(Report.patient_id == patient_id).all()
    labs = db.query(LabResult).filter(LabResult.patient_id == patient_id).all()
    notes = db.query(ClinicalNote).filter(
        ClinicalNote.patient_id == patient_id
    ).all()

    # 2️⃣ No data at all
    if not reports and not labs and not notes:
        return [{
            "severity": "INFO",
            "message": "No data found for this patient."
        }]

    # 3️⃣ Radiology text (CT / MRI / X-ray / Echo)
    radiology_text = " ".join(
        (r.content or "").lower()
        for r in reports
        if r.report_type and r.report_type.lower() in [
            "radiology", "ct", "mri", "xray", "echo"
        ]
    )

    # 4️⃣ Clinical notes
    clinical_text = " ".join(
        (n.content or "").lower()
        for n in notes
    )

    # 5️⃣ Extract labs safely
    crp = None
    wbc = None

    for lab in labs:
        if lab.test_name:
            name = lab.test_name.upper()
            if name == "CRP":
                crp = lab.value
            elif name == "WBC":
                wbc = lab.value

    # 6️⃣ Infection-negative language
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

    # 🔴 HIGH
    if infection_negative and (
        (crp is not None and crp > 100) or
        (wbc is not None and wbc > 15000)
    ):
        severity = "HIGH"
        base_message = (
            "Radiology reports no infection, but inflammatory markers "
            "are critically elevated."
        )

    # 🟠 MEDIUM
    elif infection_negative and (
        (crp is not None and 50 <= crp <= 100) or
        (wbc is not None and 11000 <= wbc <= 15000)
    ):
        severity = "MEDIUM"
        base_message = (
            "Radiology reports no infection, but inflammatory markers "
            "are moderately elevated."
        )

    # 🟢 LOW
    elif crp is not None or wbc is not None:
        severity = "LOW"
        base_message = (
            "Radiology, laboratory values, and clinical notes "
            "do not show a significant discrepancy."
        )

    # 7️⃣ No discrepancy
    if not severity:
        return [{
            "severity": "INFO",
            "message": "No clinically significant discrepancy detected."
        }]

    # 8️⃣ Prepare lab summary
    labs_summary = []
    if crp is not None:
        labs_summary.append(f"CRP: {crp} mg/L")
    if wbc is not None:
        labs_summary.append(f"WBC: {wbc} cells/mm3")

    # 9️⃣ AI explanation with fallback
    try:
        ai_explanation = generate_medical_insight(
            radiology_text=radiology_text or "No radiology findings provided.",
            labs_summary=", ".join(labs_summary) or "No abnormal lab values.",
            clinical_notes=clinical_text or "No clinical notes provided."
        )
    except Exception:
        ai_explanation = (
            "The discrepancy between imaging findings and laboratory or "
            "clinical indicators may reflect early-stage infection, "
            "limited imaging sensitivity, or a non-infectious inflammatory "
            "process. Clinical correlation is advised."
        )

    # 🔟 Store alert
    alert = Alert(
        patient_id=patient_id,
        severity=severity,
        message=f"{base_message} {ai_explanation}"
    )

    db.add(alert)
    db.commit()

    # 1️⃣1️⃣ Final response
    return [{
        "patient_id": patient_id,
        "severity": severity,
        "message": alert.message
    }]
