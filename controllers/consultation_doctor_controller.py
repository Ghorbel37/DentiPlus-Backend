from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from dependencies.auth import RoleChecker
from dependencies.get_db import get_db
import models
from schemas.auth_schemas import User as AuthUser
from schemas.consultation_doctor_schemas import Consultation, ConsultationListElement, DoctorNoteUpdate
from typing import List

router = APIRouter(prefix="/consultation-doctors", tags=["Consultation Doctors"])

# Dependency to ensure the user is a doctor
allow_doctor = RoleChecker([models.RoleUser.DOCTOR])

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
    Validate a consultation by setting etat to VALIDE and adding a doctor_note,
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
                       or etat is not EN_ATTENTE.
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

    consultation.etat = models.EtatConsultation.VALIDE
    consultation.doctor_note = note_data.doctor_note

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
    Mark a consultation for reconsultation by setting etat to RECONSULTATION and adding a doctor_note,
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
                       or etat is not EN_ATTENTE.
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

    consultation.etat = models.EtatConsultation.RECONSULTATION
    consultation.doctor_note = note_data.doctor_note

    db.add(consultation)
    db.commit()
    db.refresh(consultation)

    return consultation