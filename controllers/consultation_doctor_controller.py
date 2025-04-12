from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from dependencies.auth import RoleChecker
from dependencies.get_db import get_db
import models
from schemas.auth_schemas import User as AuthUser
from schemas.consultation_doctor_schemas import Consultation, ConsultationListElement, DoctorNoteUpdate
from typing import List

from services.llm_service import improve_doctor_note

router = APIRouter(prefix="/consultation-doctor", tags=["Consultation Doctor"])

# Dependency to ensure the user is a doctor
allow_doctor = RoleChecker([models.RoleUser.DOCTOR])

# Helper function to map sender_type to role
def map_sender_to_role(sender_type: models.MessageSenderType) -> str:
    if sender_type == models.MessageSenderType.USER:
        return "user"
    elif sender_type == models.MessageSenderType.ASSISTANT:
        return "assistant"
    else:
        return "system"  # Default fallback

@router.get("/consultations", response_model=List[ConsultationListElement])
async def get_all_doctor_consultations(
    current_user: AuthUser = Depends(allow_doctor),
    db: Session = Depends(get_db)
):
    """
    Retrieve all consultations linked to the authenticated doctor.
    
    Args:
        current_user: The authenticated doctor (via dependency).
        db: The database session (via dependency).
    
    Returns:
        A list of ConsultationListElement objects.
    
    Raises:
        HTTPException: If no consultations are found.
    """
    consultations = db.query(models.Consultation).filter(
        models.Consultation.doctor_id == current_user.id
    ).all()
    if not consultations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No consultations found for this doctor"
        )
    return consultations

@router.get("/consultations/by-etat/{etat}", response_model=List[ConsultationListElement])
async def get_doctor_consultations_by_etat(
    etat: models.EtatConsultation,
    current_user: AuthUser = Depends(allow_doctor),
    db: Session = Depends(get_db)
):
    """
    Retrieve consultations for the authenticated doctor filtered by etat.
    
    Args:
        etat: The consultation state (VALIDE, EN_ATTENTE, or RECONSULTATION).
        current_user: The authenticated doctor (via dependency).
        db: The database session (via dependency).
    
    Returns:
        A list of ConsultationListElement objects.
    
    Raises:
        HTTPException: If no consultations are found for the given etat.
    """
    consultations = db.query(models.Consultation).filter(
        models.Consultation.doctor_id == current_user.id,
        models.Consultation.etat == etat
    ).all()
    if not consultations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No consultations found with etat '{etat.value}'"
        )
    return consultations

@router.patch("/consultations/{consultation_id}/validate", response_model=Consultation)
async def validate_consultation(
    consultation_id: int,
    note_data: DoctorNoteUpdate,
    current_user: AuthUser = Depends(allow_doctor),
    db: Session = Depends(get_db)
):
    """
    Validate a consultation by setting etat to VALIDE and adding an improved doctor_note,
    but only if the current etat is EN_ATTENTE.
    
    Args:
        consultation_id: The ID of the consultation to validate.
        note_data: The request body containing the doctor_note.
        current_user: The authenticated doctor (via dependency).
        db: The database session (via dependency).
    
    Returns:
        The updated Consultation object.
    
    Raises:
        HTTPException: If the consultation is not found, not authorized,
                       etat is not EN_ATTENTE, or LLM processing fails.
    """
    consultation = db.query(models.Consultation).filter(
        models.Consultation.id == consultation_id,
        models.Consultation.doctor_id == current_user.id
    ).first()
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found or not authorized"
        )

    # Check if etat is EN_ATTENTE
    if consultation.etat != models.EtatConsultation.EN_ATTENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consultation must be in EN_ATTENTE state to be validated"
        )

    # Fetch the full chat history
    chat_history_db = consultation.chat_messages
    if not chat_history_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No chat history found for this consultation"
        )

    # Convert to list of dictionaries for LLM
    chat_history = [
        {"role": map_sender_to_role(msg.sender_type), "content": msg.content}  # Assuming sender_type is 'user' or 'assistant'
        for msg in chat_history_db
    ]

    # Check if doctor_note is empty
    improved_note = None
    if note_data.doctor_note and note_data.doctor_note.strip():
        # Improve the doctor’s note using the LLM
        try:
            improved_note = improve_doctor_note(
                etat=models.EtatConsultation.VALIDE.value,
                doctor_note=note_data.doctor_note,
                chat_history=chat_history
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error improving doctor note with LLM: {str(e)}"
            )

    # Update consultation
    consultation.etat = models.EtatConsultation.VALIDE
    consultation.doctor_note = improved_note

    db.add(consultation)
    db.commit()
    db.refresh(consultation)

    return consultation

@router.patch("/consultations/{consultation_id}/reconsultation", response_model=Consultation)
async def mark_reconsultation(
    consultation_id: int,
    note_data: DoctorNoteUpdate,
    current_user: AuthUser = Depends(allow_doctor),
    db: Session = Depends(get_db)
):
    """
    Mark a consultation for reconsultation by setting etat to RECONSULTATION and adding an improved doctor_note,
    but only if the current etat is EN_ATTENTE.
    
    Args:
        consultation_id: The ID of the consultation to mark.
        note_data: The request body containing the doctor_note.
        current_user: The authenticated doctor (via dependency).
        db: The database session (via dependency).
    
    Returns:
        The updated Consultation object.
    
    Raises:
        HTTPException: If the consultation is not found, not authorized,
                       etat is not EN_ATTENTE, or LLM processing fails.
    """
    consultation = db.query(models.Consultation).filter(
        models.Consultation.id == consultation_id,
        models.Consultation.doctor_id == current_user.id
    ).first()
    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found or not authorized"
        )

    # Check if etat is EN_ATTENTE
    if consultation.etat != models.EtatConsultation.EN_ATTENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consultation must be in EN_ATTENTE state to be marked for reconsultation"
        )

    # Fetch the full chat history
    chat_history_db = consultation.chat_messages
    if not chat_history_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No chat history found for this consultation"
        )

    # Convert to list of dictionaries for LLM
    chat_history = [
        {"role": map_sender_to_role(msg.sender_type), "content": msg.content}  # Assuming sender_type is 'user' or 'assistant'
        for msg in chat_history_db
    ]

    # Check if doctor_note is empty
    improved_note = None
    if note_data.doctor_note and note_data.doctor_note.strip():
        # Improve the doctor’s note using the LLM
        try:
            improved_note = improve_doctor_note(
                etat=models.EtatConsultation.RECONSULTATION.value,
                doctor_note=note_data.doctor_note,
                chat_history=chat_history
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error improving doctor note with LLM: {str(e)}"
            )

    # Update consultation
    consultation.etat = models.EtatConsultation.RECONSULTATION
    consultation.doctor_note = improved_note

    db.add(consultation)
    db.commit()
    db.refresh(consultation)

    return consultation