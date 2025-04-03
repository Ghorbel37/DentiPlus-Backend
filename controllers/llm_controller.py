from fastapi import APIRouter
from services.llm import diagnose_patient_en, diagnose_patient_fr
import schemas

router = APIRouter()

@router.post("/diagnose-en")
def diagnose_en(request: schemas.SymptomRequest):
    return diagnose_patient_en(request.symptoms, request.additional_details)

@router.post("/diagnose-fr")
def diagnose_fr(request: schemas.SymptomRequest):
    return diagnose_patient_fr(request.symptoms, request.additional_details)