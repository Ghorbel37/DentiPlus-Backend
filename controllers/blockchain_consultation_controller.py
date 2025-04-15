from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies.get_db import get_db
from services.blockchain_consultation_service import add_diagnosis, get_diagnosis, DiagnosisRequest
from schemas.auth_schemas import User as AuthUser
from dependencies.auth import get_current_active_user
import models

router = APIRouter(prefix="/blockchain", tags=["Blockchain"])

@router.post("/add-diagnosis")
async def add_diagnosis_blockchain(
    diagnosis: DiagnosisRequest,
    current_user: AuthUser = Depends(get_current_active_user)
    ):
    """
    Adds a diagnosis to the blockchain.
    """
    try:
        result = add_diagnosis(diagnosis)
        return {
            "message": "Diagnosis added successfully",
            "transaction_hash": result["transaction_hash"],
            "status": "Success" if result["status"] == 1 else "Failed"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add diagnosis: {str(e)}")

@router.get("/get-diagnosis/{diagnosis_id}")
async def get_diagnosis_blockchain(
    diagnosis_id: int,
    current_user: AuthUser = Depends(get_current_active_user)
    ):
    """
    Retrieves a diagnosis from the blockchain by diagnosis ID.
    """
    try:
        result = get_diagnosis(diagnosis_id)
        return {
            "message": "Diagnosis retrieved successfully",
            "diagnosis": result
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve diagnosis: {str(e)}")
    
@router.get("/verify-integrity/{consultation_id}")
async def verify_consultation_integrity(
    consultation_id: int,
    current_user: AuthUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)):
    """
    Verifies consultation integrity by comparing database and blockchain data.
    """
    try:
        # Fetch consultation from database
        consultation = db.query(models.Consultation).filter(models.Consultation.id == consultation_id).first()
        if not consultation:
            raise HTTPException(status_code=404, detail="Consultation not found")

        # Check hypotheses
        hypotheses = consultation.hypotheses
        if not hypotheses:
            raise HTTPException(status_code=400, detail="No hypotheses found")

        # Fetch diagnosis from blockchain
        blockchain_diagnosis = get_diagnosis(consultation_id)

        # Compare data
        is_valid = (
            consultation.diagnosis == blockchain_diagnosis["doctor_diagnosis"] and
            consultation.patient_id == blockchain_diagnosis["patient_id"] and
            consultation.doctor_id == blockchain_diagnosis["doctor_id"]
        )

        # Compare hypotheses (up to 3)
        for i, hypo in enumerate(hypotheses[:3]):
            condition_field = f"condition{i+1}"
            confidence_field = f"confidence{i+1}"
            if (hypo.condition != blockchain_diagnosis[condition_field] or
                hypo.confidence != blockchain_diagnosis[confidence_field]):
                is_valid = False
                break

        return {
            "message": "Integrity verification completed",
            "consultation_id": consultation_id,
            "is_valid": is_valid
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify integrity: {str(e)}")