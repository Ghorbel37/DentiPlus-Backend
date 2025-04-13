from fastapi import APIRouter
from services.storage_blockchain_service import get_value, set_value, get_accounts

router = APIRouter(prefix="/blockchain_storage", tags=["Blockchain"])

@router.get("/get-value")
async def get_value_blockchain():
    return get_value()

@router.post("/set-value/{new_value}")
def set_value_blockchain(new_value: int):
    return set_value(new_value)

@router.get("/accounts")
async def get_accounts_blockchain():
    return get_accounts()