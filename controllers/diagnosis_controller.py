from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies.get_db import get_db
from schemas.diagnosis_schemas import (ConsultationResponse, ConsultationCreate, ChatMessageResponse,
                          ConversationHistoryCreate, EtatConsultation, MessageSenderType)
from models import Consultation, ChatMessage, Hypothese, Symptoms, Patient, Doctor
import services.llm_service as llm_service  # Hypothetical LLM service

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])

# Get all diagnostics by patient
@router.get("/patient/{patient_id}", response_model=list[ConsultationResponse])
def get_all_diags_by_patient(patient_id: int, db: Session = Depends(get_db)):
    diagnostics = db.query(Consultation).filter(Consultation.patient_id == patient_id).all()
    if not diagnostics:
        raise HTTPException(status_code=404, detail="No diagnostics found for this patient")
    return diagnostics

# Get all diagnostics by patient and etat
@router.get("/patient/{patient_id}/etat/{etat}", response_model=list[ConsultationResponse])
def get_all_diags_by_patient_and_etat(patient_id: int, etat: EtatConsultation, db: Session = Depends(get_db)):
    diagnostics = db.query(Consultation).filter(Consultation.patient_id == patient_id, Consultation.etat == etat).all()
    if not diagnostics:
        raise HTTPException(status_code=404, detail="No diagnostics found for this patient and state")
    return diagnostics

# Get all diagnostics by etat
@router.get("/etat/{etat}", response_model=list[ConsultationResponse])
def get_all_diags_by_etat(etat: EtatConsultation, db: Session = Depends(get_db)):
    diagnostics = db.query(Consultation).filter(Consultation.etat == etat).all()
    if not diagnostics:
        raise HTTPException(status_code=404, detail="No diagnostics found for this state")
    return diagnostics

# Get diagnostic for patient by ID (shows chat)
@router.get("/patient/{diagnostic_id}", response_model=ConsultationResponse)
def get_diagnostic_for_patient_by_id(diagnostic_id: int, db: Session = Depends(get_db)):
    diagnostic = db.query(Consultation).filter(Consultation.id == diagnostic_id).first()
    if not diagnostic:
        raise HTTPException(status_code=404, detail="Diagnostic not found")
    return diagnostic

# Get diagnostic for doctor by ID (shows all info)
@router.get("/doctor/{diagnostic_id}", response_model=ConsultationResponse)
def get_diagnostic_for_doctor_by_id(diagnostic_id: int, db: Session = Depends(get_db)):
    diagnostic = db.query(Consultation).filter(Consultation.id == diagnostic_id).first()
    if not diagnostic:
        raise HTTPException(status_code=404, detail="Diagnostic not found")
    return diagnostic

# Create diagnostic for patient
@router.post("/", response_model=ConsultationResponse)
def create_diagnostic_for_patient(diagnostic: ConsultationCreate, db: Session = Depends(get_db)):
    # Validate patient and doctor existence
    patient = db.query(Patient).filter(Patient.id == diagnostic.patient_id).first()
    doctor = db.query(Doctor).filter(Doctor.id == diagnostic.doctor_id).first()
    if not patient or not doctor:
        raise HTTPException(status_code=404, detail="Patient or Doctor not found")

    db_diagnostic = Consultation(**diagnostic.dict())
    db.add(db_diagnostic)
    db.commit()
    db.refresh(db_diagnostic)
    
    # Create empty chat message
    empty_message = ChatMessage(
        consultation_id=db_diagnostic.id,
        content="Conversation started",
        sender_type=MessageSenderType.SYSTEM
    )
    db.add(empty_message)
    db.commit()
    return db_diagnostic

# Get all conversation history for diagnostic
@router.get("/{diagnostic_id}/conversation", response_model=list[ChatMessageResponse])
def get_all_conversation_history_for_diagnostic(diagnostic_id: int, db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(ChatMessage.consultation_id == diagnostic_id).all()
    if not messages:
        raise HTTPException(status_code=404, detail="No conversation history found")
    return messages

# Create conversation history
@router.post("/conversation/", response_model=ChatMessageResponse)
def create_conversation_history(message: ConversationHistoryCreate, db: Session = Depends(get_db)):
    db_message = ChatMessage(**message.dict())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

# Add conversation history (with LLM inference)
@router.post("/{diagnostic_id}/add-conversation", response_model=ChatMessageResponse)
def add_conversation_history(diagnostic_id: int, message: ConversationHistoryCreate, db: Session = Depends(get_db)):
    # Validate diagnostic existence
    diagnostic = db.query(Consultation).filter(Consultation.id == diagnostic_id).first()
    if not diagnostic:
        raise HTTPException(status_code=404, detail="Diagnostic not found")
    
    # Save user question
    message.consultation_id = diagnostic_id  # Ensure consultation_id is set
    user_message = create_conversation_history(message, db)

    # Run LLM inference
    llm_response = llm_service.generate_response(message.content)  # Hypothetical LLM call
    if llm_response:
        llm_message = ConversationHistoryCreate(
            consultation_id=diagnostic_id,
            content=llm_response,
            sender_type=MessageSenderType.ASSISTANT
        )
        return create_conversation_history(llm_message, db)
    raise HTTPException(status_code=500, detail="LLM response failed")

# Finish conversation for diagnostic
@router.put("/{diagnostic_id}/finish", response_model=ConsultationResponse)
def finish_conversation_for_diagnostic(diagnostic_id: int, db: Session = Depends(get_db)):
    diagnostic = db.query(Consultation).filter(Consultation.id == diagnostic_id).first()
    if not diagnostic:
        raise HTTPException(status_code=404, detail="Diagnostic not found")
    
    # Get conversation history
    messages = db.query(ChatMessage).filter(ChatMessage.consultation_id == diagnostic_id).all()
    conversation_text = " ".join([msg.content for msg in messages])
    
    # Generate summary and extract data using LLM
    diagnostic.chat_summary = llm_service.generate_summary(conversation_text)
    symptoms = llm_service.extract_symptoms(conversation_text)
    hypotheses = llm_service.extract_hypotheses(conversation_text)
    
    # Save symptoms
    for symptom in symptoms:
        db_symptom = Symptoms(
            symptom=symptom,
            user_id=diagnostic.patient.user_id,
            consultation_id=diagnostic_id
        )
        db.add(db_symptom)
    
    # Save hypotheses
    for hypothesis in hypotheses[:3]:  # Limit to 3
        db_hypothesis = Hypothese(
            condition=hypothesis["condition"],
            confidence=hypothesis["confidence"],
            consultation_id=diagnostic_id
        )
        db.add(db_hypothesis)
    
    db.commit()
    db.refresh(diagnostic)
    return diagnostic

# Respond to consultation
@router.put("/{diagnostic_id}/respond", response_model=ConsultationResponse)
def respond_to_consultation(diagnostic_id: int, etat: EtatConsultation, doctor_note: str, db: Session = Depends(get_db)):
    diagnostic = db.query(Consultation).filter(Consultation.id == diagnostic_id).first()
    if not diagnostic:
        raise HTTPException(status_code=404, detail="Diagnostic not found")
    
    if etat not in [EtatConsultation.VALIDE, EtatConsultation.RECONSULTATION]:
        raise HTTPException(status_code=400, detail="Etat must be VALIDE or RECONSULTATION")
    
    # Update etat and diagnostique
    diagnostic.etat = etat
    diagnostic.diagnostique = doctor_note
    
    # Generate final doctor message
    doctor_message_content = llm_service.generate_doctor_message(doctor_note)
    final_message = ChatMessage(
        consultation_id=diagnostic_id,
        content=doctor_message_content,
        sender_type=MessageSenderType.DOCTOR
    )
    db.add(final_message)
    
    db.commit()
    db.refresh(diagnostic)
    return diagnostic