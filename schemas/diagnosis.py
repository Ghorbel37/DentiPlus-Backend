from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from typing import List

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