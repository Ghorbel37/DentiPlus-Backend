"""Contains the methods that communicate with the LLM FastAPI"""
import requests
from dependencies.env import BASE_URL
from typing import List, Dict

from schemas.llm_service_schemas import DiagnosisResponse, CombinedResponse

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

def process_chat_history(chat_history: List[Dict[str, str]]) -> CombinedResponse:
    """
    Sends the chat history to the Colab server to extract symptoms, conditions, and summarize the chat in a single request.

    Args:
        chat_history: List of messages, each with 'role' and 'content' keys.
    
    Returns:
        CombinedResponse containing the extracted symptoms, conditions, and summary.
    
    Raises:
        Exception: If the request fails or the server returns an error.
    """
    url = f"{BASE_URL}/process_chat"
    data = {"chat_history": chat_history}

    response = requests.post(url, json=data)

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}, {response.text}")

    return CombinedResponse(**response.json())

def chat_with_model(chat_history: List[Dict[str, str]]) -> str:
    """
    Sends the chat history to the model and returns its conversational response.

    Args:
        chat_history: List of messages, each with 'role' and 'content' keys, including the user's latest prompt.
    
    Returns:
        The model's response as a string.
    
    Raises:
        Exception: If the request fails or the server returns an error.
    """
    url = f"{BASE_URL}/chat"
    data = {"chat_history": chat_history}

    response = requests.post(url, json=data)

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}, {response.text}")

    return response.json()["response"]

def improve_doctor_note(etat: str, doctor_note: str, chat_history: List[Dict[str, str]]) -> str:
    """
    Sends the consultation status, doctor’s note, and chat history to the Colab server to generate an improved version of the note.

    Args:
        etat: The status of the consultation (e.g., 'VALIDE', 'EN_ATTENTE').
        doctor_note: The doctor’s original note to be improved.
        chat_history: List of messages, each with 'role' and 'content' keys.
    
    Returns:
        The improved doctor’s note as a string.
    
    Raises:
        Exception: If the request fails or the server returns an error.
    """
    url = f"{BASE_URL}/improve_note"
    data = {
        "etat": etat,
        "doctor_note": doctor_note,
        "chat_history": chat_history
    }

    response = requests.post(url, json=data)

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}, {response.text}")

    return response.json()["improved_note"]