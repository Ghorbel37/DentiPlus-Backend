"""Contains pydantic schemas for validation"""
from typing import List, Optional
from datetime import date,datetime
from pydantic import BaseModel


class PatientBase(BaseModel):
    name: str
    birthdate: Optional[date] = None

class PatientCreate(PatientBase):
    pass

class Patient(PatientBase):
    id: int
    class Config:
        from_attributes = True

class DiagnosisBase(BaseModel):
    condition1: str
    confidence1: int
    condition2: str
    confidence2: int
    condition3: str
    confidence3: int
    doctorDiagnosis: Optional[str] = None
    patientId: int

class DiagnosisCreate(DiagnosisBase):
    pass

class Diagnosis(DiagnosisBase):
    id: int
    date: datetime

    class Config:
        from_attributes = True

class SymptomRequest(BaseModel):
    symptoms: List[str]
    additional_details: str = "None"
