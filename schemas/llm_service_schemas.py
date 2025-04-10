from typing import Dict, List
from pydantic import BaseModel

class SymptomRequest(BaseModel):
    symptoms: List[str]
    additional_details: str = "None"

class DiagnosisResponse(BaseModel):
    diagnosis: List[Dict]

class Symptom(BaseModel):
    symptom: str

class SymptomsResponse(BaseModel):
    symptoms: List[Symptom]

class Condition(BaseModel):
    condition: str
    confidence: int

class ConditionsResponse(BaseModel):
    diagnosis: List[Condition]

class ChatRequest(BaseModel):
    message: str