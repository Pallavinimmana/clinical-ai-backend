from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class ReportCreate(BaseModel):
    patient_id: str
    report_type: str
    content: str

class AlertResponse(BaseModel):
    id: str
    patient_id: str
    severity: str
    message: str

class LabCreate(BaseModel):
    patient_id: str
    test_name: str
    value: float
    unit: str
