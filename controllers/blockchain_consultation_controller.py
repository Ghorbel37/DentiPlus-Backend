from fastapi import APIRouter, HTTPException
from services.blockchain_consultation_service import add_diagnosis, get_diagnosis, DiagnosisRequest

router = APIRouter()

@router.post("/add-diagnosis")
async def add_diagnosis_blockchain(diagnosis: DiagnosisRequest):
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
async def get_diagnosis_blockchain(diagnosis_id: int):
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