from sqlalchemy import Column, String
from .database import Base
import uuid
from sqlalchemy import Column, String, Float
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    password = Column(String)

from sqlalchemy import Column, String, Text, ForeignKey
import uuid

class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, nullable=False)
    report_type = Column(String)  # radiology / clinical
    content = Column(Text)

from sqlalchemy import Column, String, Text
import uuid

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, nullable=False)
    severity = Column(String)      # LOW / MEDIUM / HIGH
    message = Column(Text)         # Explanation

class LabResult(Base):
    __tablename__ = "lab_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, nullable=False)
    test_name = Column(String)
    value = Column(Float)
    unit = Column(String)
