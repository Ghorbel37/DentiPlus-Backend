"""Contains the methods that communicate with the Blockchain"""
from fastapi import HTTPException
from pydantic import BaseModel
from web3 import Web3
from dependencies.env import BLOCKCHAIN_URL, CONTRACT_ADDRESS, ACCOUNT, PRIVATE_KEY

class SetValueRequest(BaseModel):
    value: int
    sender_address: str  # Use one of the addresses from Hardhat node output

#Sepolia
# CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
# Configure Web3
w3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_URL))
# w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545')) # HardHat

# Public address
account = ACCOUNT
# account = w3.eth.accounts[0] # If using HardHat selects first account
private_key = PRIVATE_KEY

CONTRACT_ABI = [{
    "inputs": [],
    "name": "get",
    "outputs": [{
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
    }],
    "stateMutability": "view",
    "type": "function"
}, {
    "inputs": [{
        "internalType": "uint256",
        "name": "x",
        "type": "uint256"
    }],
    "name": "set",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
}]

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

def get_value():
    try:
        value = contract.functions.get().call()
        return {"value": value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def set_value(new_value: int):
    tx = contract.functions.set(new_value).build_transaction({
        "from": account,
        "nonce": w3.eth.get_transaction_count(account),
        "gas": 2000000,
        "gasPrice": w3.to_wei("50", "gwei")
    })
    
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)

    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return {"transaction_hash": tx_hash.hex(), "status": tx_receipt.status}

def get_accounts():
    try:
        accounts = w3.eth.accounts
        return {"accounts": accounts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))