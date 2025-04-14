"""Contains the methods that communicate with the Blockchain"""
from fastapi import HTTPException
from pydantic import BaseModel
from web3 import Web3
from dependencies.env import BLOCKCHAIN_URL, DIAGNOSIS_CONTRACT_ADDRESS, ACCOUNT, PRIVATE_KEY

#Sepolia
# Configure Web3
w3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_URL))
# w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545')) # HardHat

# Public address
account = ACCOUNT
# account = w3.eth.accounts[0] # If using HardHat selects first account
private_key = PRIVATE_KEY

CONTRACT_ABI = [{ "anonymous": False, "inputs": [ { "indexed": True, "internalType": "uint256", "name": "diagnosisId", "type": "uint256" }, { "indexed": False, "internalType": "uint256", "name": "patientId", "type": "uint256" }, { "indexed": False, "internalType": "uint256", "name": "doctorId", "type": "uint256" } ], "name": "DiagnosisAdded", "type": "event" }, { "anonymous": False, "inputs": [ { "indexed": True, "internalType": "uint256", "name": "diagnosisId", "type": "uint256" }, { "indexed": False, "internalType": "string", "name": "hash", "type": "string" } ], "name": "DiagnosisRecorded", "type": "event" }, { "inputs": [ { "internalType": "uint256", "name": "_diagnosisId", "type": "uint256" }, { "internalType": "string", "name": "_condition1", "type": "string" }, { "internalType": "uint256", "name": "_confidence1", "type": "uint256" }, { "internalType": "string", "name": "_condition2", "type": "string" }, { "internalType": "uint256", "name": "_confidence2", "type": "uint256" }, { "internalType": "string", "name": "_condition3", "type": "string" }, { "internalType": "uint256", "name": "_confidence3", "type": "uint256" }, { "internalType": "string", "name": "_doctorDiagnosis", "type": "string" }, { "internalType": "uint256", "name": "_patientId", "type": "uint256" }, { "internalType": "uint256", "name": "_doctorId", "type": "uint256" } ], "name": "addDiagnosis", "outputs": [], "stateMutability": "nonpayable", "type": "function" }, { "inputs": [ { "internalType": "uint256", "name": "diagnosisId", "type": "uint256" } ], "name": "getDiagnosis", "outputs": [ { "internalType": "string", "name": "", "type": "string" }, { "internalType": "uint256", "name": "", "type": "uint256" }, { "internalType": "string", "name": "", "type": "string" }, { "internalType": "uint256", "name": "", "type": "uint256" }, { "internalType": "string", "name": "", "type": "string" }, { "internalType": "uint256", "name": "", "type": "uint256" }, { "internalType": "string", "name": "", "type": "string" }, { "internalType": "uint256", "name": "", "type": "uint256" }, { "internalType": "uint256", "name": "", "type": "uint256" }, { "internalType": "uint256", "name": "", "type": "uint256" } ], "stateMutability": "view", "type": "function" }, { "inputs": [], "name": "getDiagnosisCount", "outputs": [ { "internalType": "uint256", "name": "", "type": "uint256" } ], "stateMutability": "view", "type": "function" }, { "inputs": [ { "internalType": "uint256", "name": "diagnosisId", "type": "uint256" } ], "name": "getDiagnosisHash", "outputs": [ { "internalType": "string", "name": "", "type": "string" }, { "internalType": "uint256", "name": "", "type": "uint256" } ], "stateMutability": "view", "type": "function" }, { "inputs": [ { "internalType": "uint256", "name": "diagnosisId", "type": "uint256" }, { "internalType": "string", "name": "diagnosisHash", "type": "string" } ], "name": "storeDiagnosisHash", "outputs": [], "stateMutability": "nonpayable", "type": "function" }]

contract = w3.eth.contract(address=DIAGNOSIS_CONTRACT_ADDRESS, abi=CONTRACT_ABI)

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

def add_diagnosis(diagnosis: DiagnosisRequest):
    """
    Adds a diagnosis to the blockchain
    """
    try:
        # Build transaction for addDiagnosis with all required parameters
        tx = contract.functions.addDiagnosis(
            diagnosis.diagnosis_id,
            diagnosis.condition1,
            diagnosis.confidence1,
            diagnosis.condition2,
            diagnosis.confidence2,
            diagnosis.condition3,
            diagnosis.confidence3,
            diagnosis.doctor_diagnosis,
            diagnosis.patient_id,
            diagnosis.doctor_id
        ).build_transaction({
            "from": account,
            "nonce": w3.eth.get_transaction_count(account),
            "gas": 2000000,
            "gasPrice": w3.to_wei("50", "gwei")
        })

        # Sign and send transaction
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        return {
            "transaction_hash": tx_hash.hex(),
            "status": tx_receipt.status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_diagnosis(diagnosis_id: int):
    """
    Retrieves a diagnosis from the blockchain by diagnosis ID
    """
    try:
        # Call getDiagnosis function
        result = contract.functions.getDiagnosis(diagnosis_id).call()
        
        # Structure the response based on the ABI output
        return {
            "condition1": result[0],
            "confidence1": result[1],
            "condition2": result[2],
            "confidence2": result[3],
            "condition3": result[4],
            "confidence3": result[5],
            "doctor_diagnosis": result[6],
            "patient_id": result[7],
            "doctor_id": result[8],
            "timestamp": result[9]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))