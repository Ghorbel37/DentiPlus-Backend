from fastapi import APIRouter
from services.diagnosis_blockchain_service import add_diagnosis, get_diagnosis, DiagnosisRequest

router = APIRouter(prefix="/blockchain-diagnosis", tags=["Blockchain"])

@router.post("/add-diagnosis")
async def add_diagnosis_blockchain(diagnosis: DiagnosisRequest):
    """
    Adds a diagnosis to the blockchain
    """
    return add_diagnosis(diagnosis)

@router.get("/get-diagnosis/{index}")
async def get_diagnosis_blockchain(index: int):
    """
    Retrieves a diagnosis from the blockchain by index
    """
    return get_diagnosis(index)