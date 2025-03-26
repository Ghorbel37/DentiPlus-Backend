"""Contains the methods that communicate with the LLM FastAPI"""
import requests
from dependencies.env import BASE_URL
from pydantic import BaseModel
from typing import List, Dict

class SymptomRequest(BaseModel):
    symptoms: List[str]
    additional_details: str = "None"

class DiagnosisResponse(BaseModel):
    diagnosis: List[Dict]

def diagnose_patient_en(symptoms: List[str], additional_details: str = "None") -> DiagnosisResponse:
    url = f"{BASE_URL}/diagnose-en"
    data = {"symptoms": symptoms, "additional_details": additional_details}

    response = requests.post(url, json=data)

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}, {response.text}")

    return DiagnosisResponse(**response.json())

def diagnose_patient_fr(symptoms: List[str], additional_details: str = "None") -> DiagnosisResponse:
    url = f"{BASE_URL}/diagnose-fr"
    data = {"symptoms": symptoms, "additional_details": additional_details}

    response = requests.post(url, json=data)

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}, {response.text}")

    return DiagnosisResponse(**response.json())
