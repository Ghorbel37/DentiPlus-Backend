from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from dependencies.auth import RoleChecker
from dependencies.get_db import get_db
import models
from schemas.auth_schemas import User as AuthUser
from schemas.consultation_schemas import Consultation, ConsultationListElement, ConsultationCreate, ChatMessageCreate, ChatMessage
from typing import List

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

    # Create an associated appointment (initially empty, with default state)
    new_appointment = models.Appointment(
        dateAppointment=datetime.utcnow(),  # Placeholder; adjust as needed
        etat=models.EtatAppointment.PLANIFIE,
        consultation_id=new_consultation.id
    )
    db.add(new_appointment)
    db.commit()

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