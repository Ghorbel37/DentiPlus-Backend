"""Contains the methods that communicate with the LLM FastAPI"""
import requests
from dependencies.env import BASE_URL
from typing import List, Dict

from schemas.llm_service_schemas import ConditionsResponse, DiagnosisResponse, SymptomsResponse

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

def extract_symptoms(chat_history: List[Dict[str, str]]) -> SymptomsResponse:
    """
    Extracts symptoms from the chat history by sending a request to the Colab server.

    Args:
        chat_history: List of messages, each with 'role' and 'content' keys (e.g., [{"role": "user", "content": "I have a toothache"}]).
    
    Returns:
        SymptomsResponse containing the extracted symptoms.
    
    Raises:
        Exception: If the request fails or the server returns an error.
    """
    url = f"{BASE_URL}/extract_symptoms"
    data = {"chat_history": chat_history}

    response = requests.post(url, json=data)

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}, {response.text}")

    return SymptomsResponse(**response.json())

def extract_conditions(chat_history: List[Dict[str, str]]) -> ConditionsResponse:
    """
    Extracts conditions from the chat history by sending a request to the Colab server.

    Args:
        chat_history: List of messages, each with 'role' and 'content' keys.
    
    Returns:
        ConditionsResponse containing the extracted conditions with confidence scores.
    
    Raises:
        Exception: If the request fails or the server returns an error.
    """
    url = f"{BASE_URL}/extract_conditions"
    data = {"chat_history": chat_history}

    response = requests.post(url, json=data)

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}, {response.text}")

    return ConditionsResponse(**response.json())

def summarize_chat(chat_history: List[Dict[str, str]]) -> str:
    """
    Summarizes the chat history into a concise text summary.

    Args:
        chat_history: List of messages, each with 'role' and 'content' keys.
    
    Returns:
        A string containing the summary of the chat.
    
    Raises:
        Exception: If the request fails or the server returns an error.
    """
    url = f"{BASE_URL}/summarize"
    data = {"chat_history": chat_history}

    response = requests.post(url, json=data)

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}, {response.text}")

    return response.json()["summary"]

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