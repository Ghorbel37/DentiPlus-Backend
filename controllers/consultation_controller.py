from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from dependencies.auth import RoleChecker
from dependencies.get_db import get_db
import models
from schemas.auth_schemas import User as AuthUser
from schemas.consultation_schemas import Consultation, ConsultationListElement, ConsultationCreate, ChatMessageCreate, ChatMessage
from typing import List

from schemas.llm_service_schemas import ChatRequest
from services.llm_service import chat_with_model, extract_conditions, extract_symptoms, summarize_chat

router = APIRouter(prefix="/consultations", tags=["Consultations"])

# Dependency to ensure the user is a patient
allow_patient = RoleChecker([models.RoleUser.PATIENT])
allow_doctor = RoleChecker([models.RoleUser.DOCTOR])
allow_both = RoleChecker([models.RoleUser.PATIENT, models.RoleUser.DOCTOR])

# Helper function to get the single doctor (assuming only one doctor exists)
def get_single_doctor(db: Session) -> models.Doctor:
    doctor = db.query(models.Doctor).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="No doctor found in the system")
    return doctor

@router.post("/", response_model=Consultation)
async def create_consultation(
    consultation_data: ConsultationCreate,
    current_user: AuthUser = Depends(allow_patient),
    db: Session = Depends(get_db)
):
    # Get patient from the current user
    patient = db.query(models.Patient).filter(models.Patient.id == current_user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found for this user")

    # Get the single doctor
    doctor = get_single_doctor(db)

    # Create a new consultation
    new_consultation = models.Consultation(
        etat=models.EtatConsultation.EN_ATTENTE,  # Default state
        doctor_id=doctor.id,
        patient_id=patient.id,
        diagnosis=consultation_data.diagnosis,
        chat_summary=consultation_data.chat_summary,
        doctor_note=consultation_data.doctor_note,
        fraisAdministratives=consultation_data.fraisAdministratives,
        prix=consultation_data.prix
    )
    db.add(new_consultation)
    db.commit()
    db.refresh(new_consultation)

    # # Create an associated appointment (initially empty, with default state)
    # new_appointment = models.Appointment(
    #     dateAppointment=datetime.utcnow(),  # Placeholder; adjust as needed
    #     etat=models.EtatAppointment.PLANIFIE,
    #     consultation_id=new_consultation.id
    # )
    # db.add(new_appointment)
    # db.commit()

    return new_consultation

@router.post("/{consultation_id}/messages", response_model=ChatMessage)
async def add_chat_message(
    consultation_id: int,
    message_data: ChatMessageCreate,
    current_user: AuthUser = Depends(allow_patient),
    db: Session = Depends(get_db)
):
    # Verify the consultation exists and belongs to the patient
    consultation = db.query(models.Consultation).filter(
        models.Consultation.id == consultation_id,
        models.Consultation.patient_id == current_user.id
    ).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found or not authorized")

    # Create a new chat message
    new_message = models.ChatMessage(
        consultation_id=consultation_id,
        content=message_data.content,
        sender_type=models.MessageSenderType.USER  # Patient is the sender
    )
    db.add(new_message)

    # Send message to LLM and return response from the model

    # Save the LLM response in the db and commit
    db.commit()
    db.refresh(new_message)

    # Return the LLM response

    return new_message

@router.get("/{consultation_id}", response_model=Consultation)
async def get_consultation(
    consultation_id: int,
    current_user: AuthUser = Depends(allow_patient),
    db: Session = Depends(get_db)
):
    # Fetch the consultation and ensure it belongs to the patient
    consultation = db.query(models.Consultation).filter(
        models.Consultation.id == consultation_id,
        models.Consultation.patient_id == current_user.id
    ).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    return consultation

@router.get("/", response_model=List[ConsultationListElement])
async def get_all_consultations(
    current_user: AuthUser = Depends(allow_patient),
    db: Session = Depends(get_db)
):
    consultations = db.query(models.Consultation).filter(
        models.Consultation.patient_id == current_user.id
    ).all()
    if not consultations:
        raise HTTPException(status_code=404, detail="No consultations found")
    return consultations

@router.get("/by-etat/{etat}", response_model=List[ConsultationListElement])
async def get_all_consultations_by_etat(
    etat: models.EtatConsultation,
    current_user: AuthUser = Depends(allow_patient),
    db: Session = Depends(get_db)
):
    """
    Retrieve all consultations for the authenticated patient filtered by etat.
    """
    consultations = db.query(models.Consultation).filter(
        models.Consultation.patient_id == current_user.id,
        models.Consultation.etat == etat
    ).all()
    if not consultations:
        raise HTTPException(status_code=404, detail=f"No consultations found with etat '{etat.value}'")
    return consultations

@router.get("/{consultation_id}/chat-history", response_model=List[ChatMessage])
async def get_consultation_chat_history(
    consultation_id: int,
    current_user: AuthUser = Depends(allow_patient),
    db: Session = Depends(get_db)
):
    """
    Retrieve the chat history for a specific consultation.
    """
    # Verify the consultation exists and belongs to the patient
    consultation = db.query(models.Consultation).filter(
        models.Consultation.id == consultation_id,
        models.Consultation.patient_id == current_user.id
    ).one()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    # Fetch all chat messages for the consultation
    chat_history = db.query(models.ChatMessage).filter(
        models.ChatMessage.consultation_id == consultation_id
    ).order_by(models.ChatMessage.timestamp.asc()).all()

    if not chat_history:
        return []  # Return an empty list if no messages exist

    return chat_history

# Helper function to map sender_type to role
def map_sender_to_role(sender_type: models.MessageSenderType) -> str:
    if sender_type == models.MessageSenderType.USER:
        return "user"
    elif sender_type == models.MessageSenderType.ASSISTANT:
        return "assistant"
    else:
        return "system"  # Default fallback

@router.post("/{consultation_id}/chat", response_model=str)
async def send_message_to_consultation(
    consultation_id: int,
    request: ChatRequest,
    current_user: AuthUser = Depends(allow_patient),
    db: Session = Depends(get_db)
):
    """
    Handle a user message in a consultation chat:
    - Prepare the user's message and fetch chat history.
    - Send to the LLM and await response.
    - Save both user message and LLM response to the database only after successful LLM response.
    - Return the LLM's response.
    
    Args:
        consultation_id: The ID of the consultation.
        request: The request body containing the user's message.
        current_user: The authenticated patient (via dependency).
        db: The database session (via dependency).
    
    Returns:
        The LLM's response as a string.
    
    Raises:
        HTTPException: If the consultation is not found, user is not authorized,
                       or if there’s an error communicating with the LLM.
    """
    # Step 1: Verify the consultation exists and belongs to the patient
    consultation = db.query(models.Consultation).filter(
        models.Consultation.id == consultation_id,
        models.Consultation.patient_id == current_user.id
    ).first()
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found or not authorized"
        )

    # Step 2: Prepare user message in memory (don’t save yet)
    message = request.message
    user_message_dict = {"role": "user", "content": message}
    user_message_db = models.ChatMessage(
        consultation_id=consultation_id,
        content=message,
        sender_type=models.MessageSenderType.USER
    )

    # Step 3: Fetch the full chat history
    chat_history_db = db.query(models.ChatMessage).filter(
        models.ChatMessage.consultation_id == consultation_id
    ).order_by(models.ChatMessage.timestamp.asc()).all()

    # Convert to list of dictionaries with {"role": "user"/"assistant", "content": message}
    chat_history = [
        {"role": map_sender_to_role(msg.sender_type), "content": msg.content}
        for msg in chat_history_db
    ]

    # Append the user’s new message to the chat history for LLM
    chat_history.append(user_message_dict)

    # Step 4: Send chat history to LLM and get response
    try:
        llm_response = chat_with_model(chat_history)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with LLM: {str(e)}"
        )

    # Step 5: Prepare LLM response in memory
    assistant_message_dict = {"role": "assistant", "content": llm_response}
    assistant_message_db = models.ChatMessage(
        consultation_id=consultation_id,
        content=llm_response,
        sender_type=models.MessageSenderType.ASSISTANT
    )

    # Step 6: Save both messages to the database only after successful LLM response
    db.add(user_message_db)
    db.add(assistant_message_db)
    db.commit()
    db.refresh(user_message_db)
    db.refresh(assistant_message_db)

    # Step 7: Return the LLM’s response
    return llm_response

@router.post("/{consultation_id}/finish", response_model=Consultation)
async def finish_consultation_chat(
    consultation_id: int,
    current_user: AuthUser = Depends(allow_patient),
    db: Session = Depends(get_db)
):
    """
    Finish a consultation chat by summarizing it, extracting symptoms and conditions,
    updating the consultation in the database, and setting etat to VALIDE.
    
    Args:
        consultation_id: The ID of the consultation to finish.
        current_user: The authenticated patient (via dependency).
        db: The database session (via dependency).
    
    Returns:
        The updated Consultation object.
    
    Raises:
        HTTPException: If the consultation is not found, user is not authorized,
                       or if there’s an error communicating with the LLM.
    """
    # Step 1: Verify the consultation exists and belongs to the patient
    consultation = db.query(models.Consultation).filter(
        models.Consultation.id == consultation_id,
        models.Consultation.patient_id == current_user.id
    ).first()
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found or not authorized"
        )

    # Step 2: Fetch the full chat history
    chat_history_db = db.query(models.ChatMessage).filter(
        models.ChatMessage.consultation_id == consultation_id
    ).order_by(models.ChatMessage.timestamp.asc()).all()
    if not chat_history_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No chat history found for this consultation"
        )

    # Convert to list of dictionaries for LLM
    chat_history = [
        {"role": map_sender_to_role(msg.sender_type), "content": msg.content}
        for msg in chat_history_db
    ]

    # Step 3: Call LLM services and handle responses
    try:
        # Summarize the chat
        chat_summary = summarize_chat(chat_history)

        # Extract symptoms
        symptoms_response = extract_symptoms(chat_history)
        symptoms = symptoms_response.symptoms

        # Extract conditions
        conditions_response = extract_conditions(chat_history)
        conditions = conditions_response.diagnosis

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat with LLM: {str(e)}"
        )

    # Step 4: Prepare database updates in memory
    # Update consultation with chat summary and set etat to VALIDE
    consultation.chat_summary = chat_summary
    consultation.etat = models.EtatConsultation.EN_ATTENTE

    # Create Symptom objects
    symptom_objects = [
        models.Symptoms(
            symptom=symptom.symptom,
            user_id=current_user.id,
            consultation_id=consultation_id
        )
        for symptom in symptoms
    ]

    # Create Hypothese (condition) objects
    condition_objects = [
        models.Hypothese(
            condition=condition.condition,
            confidence=condition.confidence,
            consultation_id=consultation_id
        )
        for condition in conditions
    ]

    # Step 5: Save all changes to the database only after successful LLM responses
    for symptom_obj in symptom_objects:
        db.add(symptom_obj)
    for condition_obj in condition_objects:
        db.add(condition_obj)
    db.add(consultation)  # Update the consultation with chat_summary and etat
    db.commit()

    # Refresh the consultation to include updated relationships
    db.refresh(consultation)

    # Step 6: Return the updated consultation
    return consultation