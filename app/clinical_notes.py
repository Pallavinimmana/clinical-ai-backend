from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import ClinicalNote
from .schemas import ClinicalNoteCreate
from .auth import get_current_user

router = APIRouter(prefix="/clinical-notes", tags=["Clinical Notes"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
def add_clinical_note(
    note: ClinicalNoteCreate,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_note = ClinicalNote(
        patient_id=note.patient_id,
        content=note.content
    )
    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    return {
        "id": new_note.id,
        "patient_id": new_note.patient_id,
        "content": new_note.content
    }


@router.get("/{patient_id}")
def get_clinical_notes(
    patient_id: str,
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notes = db.query(ClinicalNote).filter(
        ClinicalNote.patient_id == patient_id
    ).all()

    return [
        {
            "id": n.id,
            "patient_id": n.patient_id,
            "content": n.content
        }
        for n in notes
    ]
