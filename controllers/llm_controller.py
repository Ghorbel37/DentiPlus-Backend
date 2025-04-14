from fastapi import APIRouter
from schemas.llm_service_schemas import SymptomRequest
from services.llm_service import diagnose_patient_en, diagnose_patient_fr

router = APIRouter()

@router.post("/diagnose-en")
def diagnose_en(request: SymptomRequest):
    return diagnose_patient_en(request.symptoms, request.additional_details)

@router.post("/diagnose-fr")
def diagnose_fr(request: SymptomRequest):
    return diagnose_patient_fr(request.symptoms, request.additional_details)