from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.background import BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from dependencies.auth import RoleChecker
from dependencies.get_db import get_db
import models
from schemas.auth_schemas import User as AuthUser
from schemas.consultation_doctor_schemas import Consultation, ConsultationDetailed, ConsultationListElement, BlockchainDiagnosisRequest, DoctorNoteUpdate, PatientInfo
from typing import List

from services.blockchain_consultation_service import add_diagnosis
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
    elif sender_type == models.MessageSenderType.DOCTOR:
        return "doctor"
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

@router.get("/consultations/{consultation_id}", response_model=ConsultationDetailed)
async def get_consultation_by_id(
    consultation_id: int,
    current_user: AuthUser = Depends(allow_doctor),
    db: Session = Depends(get_db)
):
    """
    Retrieve a consultation by ID, including patient information, symptoms, and conditions.
    
    Args:
        consultation_id: The ID of the consultation to retrieve.
        current_user: The authenticated doctor (via dependency).
        db: The database session (via dependency).
    
    Returns:
        A ConsultationDetailed object with patient, symptoms, and conditions.
    
    Raises:
        HTTPException: If the consultation is not found or not authorized.
    """
    consultation = db.query(models.Consultation).options(
        joinedload(models.Consultation.patient).joinedload(models.Patient.user),
        joinedload(models.Consultation.symptoms),
        joinedload(models.Consultation.hypotheses),
        joinedload(models.Consultation.chat_messages)
    ).filter(
        models.Consultation.id == consultation_id,
        models.Consultation.doctor_id == current_user.id
    ).first()

    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found or not authorized"
        )

    # Manually construct the PatientInfo to flatten patient and user data
    patient_info = PatientInfo(
        id=consultation.patient.id,
        name=consultation.patient.user.name,
        email=consultation.patient.user.email,
        adress=consultation.patient.user.adress,
        birthdate=consultation.patient.user.birthdate,
        phoneNumber=consultation.patient.user.phoneNumber,
        calories=consultation.patient.calories,
        frequenceCardiaque=consultation.patient.frequenceCardiaque,
        poids=consultation.patient.poids
    )

    # Construct the ConsultationDetailed response
    consultation_detailed = ConsultationDetailed(
        id=consultation.id,
        date=consultation.date,
        diagnosis=consultation.diagnosis,
        chat_summary=consultation.chat_summary,
        doctor_note=consultation.doctor_note,
        etat=consultation.etat,
        fraisAdministratives=consultation.fraisAdministratives,
        prix=consultation.prix,
        patient=patient_info,
        symptoms=consultation.symptoms,
        hypotheses=consultation.hypotheses,
        chat_messages=consultation.chat_messages
    )

    return consultation_detailed

async def add_diagnosis_to_blockchain(diagnosis_data: BlockchainDiagnosisRequest, db: Session):
    """
    Adds a diagnosis to the blockchain and handles errors with database rollback.
    
    Args:
        diagnosis_data: The diagnosis data to add to the blockchain.
        db: The database session for rollback in case of failure.
    
    Raises:
        HTTPException: If the blockchain transaction fails.
    """
    try:
        result = add_diagnosis(diagnosis_data)
        if result["status"] == 0:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Diagnosis could not be added to the blockchain: Transaction failed"
            )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add diagnosis to blockchain: {str(e)}"
        )

@router.post("/consultations/{consultation_id}/validate", response_model=Consultation)
async def validate_consultation(
    consultation_id: int,
    note_data: DoctorNoteUpdate,
    background_tasks: BackgroundTasks,
    current_user: AuthUser = Depends(allow_doctor),
    db: Session = Depends(get_db)
):
    """
    Validate a consultation by setting etat to VALIDE, updating the doctor_note,
    adding the doctor_note to the chat history with role=DOCTOR, and adding the diagnosis to the blockchain.
    """
    # Fetch consultation
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
        {"role": map_sender_to_role(msg.sender_type), "content": msg.content}
        for msg in chat_history_db
    ]

    # Improve doctor's note if provided
    improved_note = None
    if note_data.doctor_note and note_data.doctor_note.strip():
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
    consultation.doctor_note = note_data.doctor_note
    consultation.diagnosis = improved_note or consultation.diagnosis

    # Add doctor_note to chat history as a ChatMessage with role=DOCTOR
    if note_data.doctor_note and note_data.doctor_note.strip():
        doctor_message = models.ChatMessage(
            consultation_id=consultation_id,
            content=improved_note,
            sender_type=models.MessageSenderType.DOCTOR
        )
        db.add(doctor_message)

    db.add(consultation)
    db.commit()
    db.refresh(consultation)

    # Construct BlockchainDiagnosisRequest for blockchain
    hypotheses = consultation.hypotheses or []
    diagnosis_data = BlockchainDiagnosisRequest(
        diagnosis_id=consultation.id,
        patient_id=consultation.patient_id,
        doctor_id=consultation.doctor_id,
        doctor_diagnosis=consultation.diagnosis or "",
        condition1=hypotheses[0].condition if len(hypotheses) > 0 else "",
        confidence1=hypotheses[0].confidence if len(hypotheses) > 0 else 0,
        condition2=hypotheses[1].condition if len(hypotheses) > 1 else "",
        confidence2=hypotheses[1].confidence if len(hypotheses) > 1 else 0,
        condition3=hypotheses[2].condition if len(hypotheses) > 2 else "",
        confidence3=hypotheses[2].confidence if len(hypotheses) > 2 else 0
    )

    # Schedule blockchain operation
    background_tasks.add_task(add_diagnosis_to_blockchain, diagnosis_data, db)

    return consultation

@router.post("/consultations/{consultation_id}/reconsultation", response_model=Consultation)
async def mark_reconsultation(
    consultation_id: int,
    note_data: DoctorNoteUpdate,
    background_tasks: BackgroundTasks,
    current_user: AuthUser = Depends(allow_doctor),
    db: Session = Depends(get_db)
):
    """
    Mark a consultation for reconsultation by setting etat to RECONSULTATION, updating the doctor_note,
    adding the doctor_note to the chat history with role=DOCTOR, and adding the diagnosis to the blockchain.
    """
    # Fetch consultation
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
        {"role": map_sender_to_role(msg.sender_type), "content": msg.content}
        for msg in chat_history_db
    ]

    # Improve doctor's note if provided
    improved_note = None
    if note_data.doctor_note and note_data.doctor_note.strip():
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
    consultation.doctor_note = note_data.doctor_note
    consultation.diagnosis = improved_note or consultation.diagnosis

    # Add doctor_note to chat history as a ChatMessage with role=DOCTOR
    if note_data.doctor_note and note_data.doctor_note.strip():
        doctor_message = models.ChatMessage(
            consultation_id=consultation_id,
            content=improved_note,
            sender_type=models.MessageSenderType.DOCTOR
        )
        db.add(doctor_message)

    db.add(consultation)
    db.commit()
    db.refresh(consultation)

    # Construct BlockchainDiagnosisRequest for blockchain
    hypotheses = consultation.hypotheses or []
    diagnosis_data = BlockchainDiagnosisRequest(
        diagnosis_id=consultation.id,
        patient_id=consultation.patient_id,
        doctor_id=consultation.doctor_id,
        doctor_diagnosis=consultation.diagnosis or "",
        condition1=hypotheses[0].condition if len(hypotheses) > 0 else "",
        confidence1=hypotheses[0].confidence if len(hypotheses) > 0 else 0,
        condition2=hypotheses[1].condition if len(hypotheses) > 1 else "",
        confidence2=hypotheses[1].confidence if len(hypotheses) > 1 else 0,
        condition3=hypotheses[2].condition if len(hypotheses) > 2 else "",
        confidence3=hypotheses[2].confidence if len(hypotheses) > 2 else 0
    )

    # Schedule blockchain operation
    background_tasks.add_task(add_diagnosis_to_blockchain, diagnosis_data, db)

    return consultation