from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from . import models
from .auth import router as auth_router
from .patients import router as patient_router
from .reports import router as report_router
from .analysis import router as analysis_router
from .labs import router as lab_router
from .clinical_notes import router as clinical_notes_router


# ---------------- DATABASE ----------------
Base.metadata.create_all(bind=engine)

# ---------------- APP ----------------
app = FastAPI(title="AI Clinical Discrepancy System")

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ allow frontend from anywhere (Vercel + local)
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, OPTIONS, etc.
    allow_headers=["*"],
)

# ---------------- ROUTERS ----------------
app.include_router(auth_router)
app.include_router(patient_router)
app.include_router(report_router)
app.include_router(lab_router)
app.include_router(analysis_router)
app.include_router(clinical_notes_router)


# ---------------- ROOT ----------------
@app.get("/")
def root():
    return {"message": "Backend running successfully"}
