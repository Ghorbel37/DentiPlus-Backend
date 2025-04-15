from fastapi import APIRouter, Depends
from schemas.llm_service_schemas import SymptomRequest
from services.llm_service import diagnose_patient_en, diagnose_patient_fr
from schemas.auth_schemas import User as AuthUser
from dependencies.auth import get_current_active_user

router = APIRouter()

@router.post("/diagnose-en")
def diagnose_en(
    request: SymptomRequest,
    current_user: AuthUser = Depends(get_current_active_user)
    ):
    return diagnose_patient_en(request.symptoms, request.additional_details)

@router.post("/diagnose-fr")
def diagnose_fr(
    request: SymptomRequest,
    current_user: AuthUser = Depends(get_current_active_user)
    ):
    return diagnose_patient_fr(request.symptoms, request.additional_details)