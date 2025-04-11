from typing import Dict, List
from pydantic import BaseModel

class SymptomRequest(BaseModel):
    symptoms: List[str]
    additional_details: str = "None"

class DiagnosisResponse(BaseModel):
    diagnosis: List[Dict]

class Symptom(BaseModel):
    symptom: str

class Condition(BaseModel):
    condition: str
    confidence: int

class ChatRequest(BaseModel):
    message: str

class CombinedResponse(BaseModel):
    symptoms: List[Symptom]
    conditions: List[Condition]
    summary: str