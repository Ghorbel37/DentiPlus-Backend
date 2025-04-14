from pydantic.main import BaseModel

class DiagnosisRequest(BaseModel):
    diagnosis_id: int
    condition1: str
    confidence1: int
    condition2: str
    confidence2: int
    condition3: str
    confidence3: int
    doctor_diagnosis: str
    patient_id: int
    doctor_id: int