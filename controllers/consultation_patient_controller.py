from datetime import datetime, timedelta, time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, not_
from dependencies.auth import RoleChecker
from dependencies.get_db import get_db
import models
from schemas.auth_schemas import User as AuthUser
from schemas.consultation_patient_schemas import Appointment, AppointmentCreate, Consultation, ConsultationListElement, ConsultationCreate, ChatMessageCreate, ChatMessage, TimeSlot, UnavailableTimesRequest, UnavailableTimesResponse
from typing import List

from schemas.llm_service_schemas import ChatRequest
from services.blockchain_consultation_service import get_diagnosis
from services.llm_service import chat_with_model, process_chat_history

router = APIRouter(prefix="/consultation-patient", tags=["Consultation Patient"])

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
    """
    Create a new consultation for the authenticated patient, or return an existing
    EN_COURS consultation with no chat history if one exists.
    
    Args:
        consultation_data: The request body containing consultation details.
        current_user: The authenticated patient (via dependency).
        db: The database session (via dependency).
    
    Returns:
        The existing or newly created Consultation object.
    
    Raises:
        HTTPException: If the patient or doctor is not found.
    """
    # Get patient from the current user
    patient = db.query(models.Patient).filter(models.Patient.id == current_user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found for this user")

    # Check for existing EN_COURS consultation with no chat history
    existing_consultation = db.query(models.Consultation).filter(
        models.Consultation.patient_id == current_user.id,
        models.Consultation.etat == models.EtatConsultation.EN_COURS
    ).join(
        models.ChatMessage,
        models.Consultation.id == models.ChatMessage.consultation_id,
        isouter=True
    ).filter(
        models.ChatMessage.id == None
    ).first()

    if existing_consultation:
        return existing_consultation

    # Get the single doctor
    doctor = get_single_doctor(db)

    # Create a new consultation
    new_consultation = models.Consultation(
        etat=models.EtatConsultation.EN_COURS,  # En cours de consultation
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

    return new_consultation

# @router.post("/{consultation_id}/messages", response_model=ChatMessage)
# async def add_chat_message(
#     consultation_id: int,
#     message_data: ChatMessageCreate,
#     current_user: AuthUser = Depends(allow_patient),
#     db: Session = Depends(get_db)
# ):
#     # Verify the consultation exists and belongs to the patient
#     consultation = db.query(models.Consultation).filter(
#         models.Consultation.id == consultation_id,
#         models.Consultation.patient_id == current_user.id
#     ).first()
#     if not consultation:
#         raise HTTPException(status_code=404, detail="Consultation not found or not authorized")

#     # Create a new chat message
#     new_message = models.ChatMessage(
#         consultation_id=consultation_id,
#         content=message_data.content,
#         sender_type=models.MessageSenderType.USER  # Patient is the sender
#     )
#     db.add(new_message)

#     # Send message to LLM and return response from the model

#     # Save the LLM response in the db and commit
#     db.commit()
#     db.refresh(new_message)

#     # Return the LLM response

#     return new_message

# New endpoint to get all patient appointments
@router.get("/appointments", response_model=List[Appointment])
async def get_all_patient_appointments(
    current_user: AuthUser = Depends(allow_patient),
    db: Session = Depends(get_db)
):
    """
    Retrieve all appointments associated with the authenticated patient.
    
    Args:
        current_user: The authenticated patient (via dependency).
        db: The database session (via dependency).
    
    Returns:
        A list of Appointment objects.
    
    Raises:
        HTTPException: If no appointments are found.
    """
    appointments = db.query(models.Appointment).join(
        models.Consultation, models.Appointment.consultation_id == models.Consultation.id
    ).filter(
        models.Consultation.patient_id == current_user.id
    ).all()
    if not appointments:
        raise HTTPException(status_code=404, detail="No appointments found")
    return appointments

@router.get("/reconsultations/available", response_model=List[ConsultationListElement])
async def get_reconsultations_without_planifie(
    current_user: AuthUser = Depends(allow_patient),
    db: Session = Depends(get_db)
):
    """
    Retrieve all consultations for the authenticated patient that:
    - Have etat=RECONSULTATION.
    - Have no appointments or only appointments with etat != PLANIFIE.
    
    Args:
        current_user: The authenticated patient (via dependency).
        db: The database session (via dependency).
    
    Returns:
        A list of consultations matching the criteria.
    
    Raises:
        HTTPException: If no consultations are found.
    """
    # Subquery to identify consultations with PLANIFIE appointments
    planifie_subquery = db.query(models.Appointment.consultation_id).filter(
        models.Appointment.etat == models.EtatAppointment.PLANIFIE
    ).subquery()

    # Query consultations with etat=RECONSULTATION and no PLANIFIE appointments
    consultations = db.query(models.Consultation).filter(
        models.Consultation.patient_id == current_user.id,
        models.Consultation.etat == models.EtatConsultation.RECONSULTATION,
        not_(models.Consultation.id.in_(planifie_subquery))
    ).all()

    if not consultations:
        raise HTTPException(status_code=404, detail="No eligible reconsultations found")

    return consultations

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
    elif sender_type == models.MessageSenderType.DOCTOR:
        return "doctor"
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
    - Verify the consultation is in EN_COURS state.
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
                       consultation is not EN_COURS, or if there’s an error communicating with the LLM.
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

    # Step 2: Check if consultation etat is EN_COURS
    if consultation.etat != models.EtatConsultation.EN_COURS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consultation must be in EN_COURS state to send messages"
        )

    # Step 3: Prepare user message in memory (don’t save yet)
    message = request.message
    user_message_dict = {"role": "user", "content": message}
    user_message_db = models.ChatMessage(
        consultation_id=consultation_id,
        content=message,
        sender_type=models.MessageSenderType.USER
    )

    # Step 4: Fetch the full chat history
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

    # Step 5: Send chat history to LLM and get response
    try:
        llm_response = chat_with_model(chat_history)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with LLM: {str(e)}"
        )

    # Step 6: Prepare LLM response in memory
    assistant_message_dict = {"role": "assistant", "content": llm_response}
    assistant_message_db = models.ChatMessage(
        consultation_id=consultation_id,
        content=llm_response,
        sender_type=models.MessageSenderType.ASSISTANT
    )

    # Step 7: Save both messages to the database only after successful LLM response
    db.add(user_message_db)
    db.add(assistant_message_db)
    db.commit()
    db.refresh(user_message_db)
    db.refresh(assistant_message_db)

    # Step 8: Return the LLM’s response
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
                       consultation is not in EN_COURS state,
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

    # Step 2: Check if consultation is in EN_COURS state
    if consultation.etat != models.EtatConsultation.EN_COURS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consultation cannot be finished; it is not in EN_COURS state"
        )

    # Step 3: Fetch the full chat history
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

    # Step 4: Call the combined LLM service and handle response
    try:
        # Call the combined method to get symptoms, conditions, and summary
        combined_response = process_chat_history(chat_history)
        symptoms = combined_response.symptoms
        conditions = combined_response.conditions
        chat_summary = combined_response.summary

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat with LLM: {str(e)}"
        )

    # Step 5: Prepare database updates in memory
    # Update consultation with chat summary and set etat to EN_ATTENTE
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

    # Step 6: Save all changes to the database only after successful LLM response
    for symptom_obj in symptom_objects:
        db.add(symptom_obj)
    for condition_obj in condition_objects:
        db.add(condition_obj)
    db.add(consultation)  # Update the consultation with chat_summary and etat
    db.commit()

    # Refresh the consultation to include updated relationships
    db.refresh(consultation)

    # Step 7: Return the updated consultation
    return consultation

# Updated add_appointment endpoint (hourly intervals)
@router.post("/{consultation_id}/appointments", response_model=Appointment)
async def add_appointment(
    consultation_id: int,
    appointment_data: AppointmentCreate,
    current_user: AuthUser = Depends(allow_patient),
    db: Session = Depends(get_db)
):
    """
    Create a new appointment for a consultation if:
    - The consultation's etat is RECONSULTATION.
    - No existing appointment is linked to the consultation (checked via consultation.appointment).
    - The dateAppointment is at the start of an hour (e.g., 9:00, 10:00).
    - The one-hour time slot is available for the doctor.
    
    Args:
        consultation_id: The ID of the consultation.
        appointment_data: The request body containing dateAppointment.
        current_user: The authenticated patient (via dependency).
        db: The database session (via dependency).
    
    Returns:
        The created Appointment object.
    
    Raises:
        HTTPException: If the consultation is not found, user is not authorized,
                       etat is not RECONSULTATION, appointment exists,
                       time is not at the start of an hour, or slot is unavailable.
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

    # Step 2: Check if etat is RECONSULTATION
    if consultation.etat != models.EtatConsultation.RECONSULTATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consultation must be in RECONSULTATION state to add an appointment"
        )

    # Step 3: Check if a PLANIFIE appointment already exists
    planifie_appointment = db.query(models.Appointment).filter(
        models.Appointment.consultation_id == consultation_id,
        models.Appointment.etat == models.EtatAppointment.PLANIFIE
    ).first()
    if planifie_appointment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A PLANIFIE appointment is already linked to this consultation"
        )

    # Step 4: Validate hourly interval
    appointment_time = appointment_data.dateAppointment
    if appointment_time.minute != 0 or appointment_time.second != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Appointment time must be at the start of an hour (e.g., 9:00, 10:00)"
        )

    # Step 5: Check for scheduling conflicts
    appointment_end = appointment_time + timedelta(hours=1)
    conflicting_appointments = db.query(models.Appointment).join(
        models.Consultation, models.Appointment.consultation_id == models.Consultation.id
    ).filter(
        models.Consultation.doctor_id == consultation.doctor_id,
        models.Appointment.etat != models.EtatAppointment.ANNULE,
        and_(
            models.Appointment.dateAppointment < appointment_end,
            models.Appointment.dateAppointment >= appointment_time
        )
    ).all()

    if conflicting_appointments:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The selected time slot is unavailable due to a scheduling conflict"
        )

    # Step 6: Create the new appointment
    new_appointment = models.Appointment(
        dateCreation=datetime.utcnow(),
        dateAppointment=appointment_time,
        etat=models.EtatAppointment.PLANIFIE,
        consultation_id=consultation_id
    )

    # Step 7: Save to database
    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)

    # Step 8: Return the created appointment
    return new_appointment

# New endpoint to change appointment time
@router.post("/appointments/{appointment_id}/time", response_model=Appointment)
async def change_appointment_time(
    appointment_id: int,
    appointment_data: AppointmentCreate,
    current_user: AuthUser = Depends(allow_patient),
    db: Session = Depends(get_db)
):
    """
    Change the time of an existing appointment if:
    - The appointment exists and belongs to the patient's consultation.
    - The new dateAppointment is at the start of an hour (e.g., 9:00, 10:00).
    - The one-hour time slot is available for the doctor (no other PLANIFIE appointments).
    
    Args:
        appointment_id: The ID of the appointment to update.
        appointment_data: The request body containing the new dateAppointment.
        current_user: The authenticated patient (via dependency).
        db: The database session (via dependency).
    
    Returns:
        The updated Appointment object.
    
    Raises:
        HTTPException: If the appointment is not found, user is not authorized,
                       time is not at the start of an hour, or slot is unavailable.
    """
    # Step 1: Verify the appointment exists and belongs to the patient
    appointment = db.query(models.Appointment).join(
        models.Consultation, models.Appointment.consultation_id == models.Consultation.id
    ).filter(
        models.Appointment.id == appointment_id,
        models.Consultation.patient_id == current_user.id
    ).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found or not authorized"
        )

    # Step 2: Validate hourly interval
    new_time = appointment_data.dateAppointment
    if new_time.minute != 0 or new_time.second != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New appointment time must be at the start of an hour (e.g., 9:00, 10:00)"
        )

    # Step 3: Check for scheduling conflicts
    appointment_end = new_time + timedelta(hours=1)
    conflicting_appointments = db.query(models.Appointment).join(
        models.Consultation, models.Appointment.consultation_id == models.Consultation.id
    ).filter(
        models.Consultation.doctor_id == appointment.consultation.doctor_id,
        models.Appointment.etat == models.EtatAppointment.PLANIFIE,
        models.Appointment.id != appointment_id,  # Exclude the current appointment
        and_(
            models.Appointment.dateAppointment < appointment_end,
            models.Appointment.dateAppointment >= new_time
        )
    ).all()

    if conflicting_appointments:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The selected time slot is unavailable due to a scheduling conflict"
        )

    # Step 4: Update the appointment time
    appointment.dateAppointment = new_time

    # Step 5: Save to database
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    # Step 6: Return the updated appointment
    return appointment

# New endpoint to cancel appointment
@router.post("/appointments/{appointment_id}/cancel", response_model=Appointment)
async def cancel_appointment(
    appointment_id: int,
    current_user: AuthUser = Depends(allow_patient),
    db: Session = Depends(get_db)
):
    """
    Cancel an appointment by setting its etat to ANNULE.
    
    Args:
        appointment_id: The ID of the appointment to cancel.
        current_user: The authenticated patient (via dependency).
        db: The database session (via dependency).
    
    Returns:
        The updated Appointment object.
    
    Raises:
        HTTPException: If the appointment is not found, user is not authorized,
                       or the appointment is already canceled.
    """
    # Step 1: Verify the appointment exists and belongs to the patient
    appointment = db.query(models.Appointment).join(
        models.Consultation, models.Appointment.consultation_id == models.Consultation.id
    ).filter(
        models.Appointment.id == appointment_id,
        models.Consultation.patient_id == current_user.id
    ).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found or not authorized"
        )

    # Step 2: Check if the appointment is already canceled
    if appointment.etat == models.EtatAppointment.ANNULE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Appointment is already canceled"
        )

    # Step 3: Update the appointment status
    appointment.etat = models.EtatAppointment.ANNULE

    # Step 4: Save to database
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    # Step 5: Return the updated appointment
    return appointment

# Updated get_unavailable_times endpoint (hourly intervals, single doctor)
@router.post("/unavailable-times", response_model=UnavailableTimesResponse)
async def get_unavailable_times(
    request: UnavailableTimesRequest,
    current_user: AuthUser = Depends(allow_patient),
    db: Session = Depends(get_db)
):
    """
    Retrieve unavailable time slots for the single doctor on a given date.
    Time slots are hourly (e.g., 9:00, 10:00).
    
    Args:
        request: The request body containing the date.
        current_user: The authenticated patient (via dependency).
        db: The database session (via dependency).
    
    Returns:
        A list of unavailable time slots (hourly intervals).
    
    Raises:
        HTTPException: If no doctor is found in the system.
    """
    # Get the single doctor
    doctor = db.query(models.Doctor).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No doctor found in the system"
        )

    # Get start and end of the requested date
    start_date = datetime.combine(request.date, time(0, 0))
    end_date = start_date + timedelta(days=1)

    # Fetch all appointments for the doctor on the given date
    appointments = db.query(models.Appointment).join(
        models.Consultation, models.Appointment.consultation_id == models.Consultation.id
    ).filter(
        models.Consultation.doctor_id == doctor.id,
        models.Appointment.etat != models.EtatAppointment.ANNULE,
        models.Appointment.dateAppointment >= start_date,
        models.Appointment.dateAppointment < end_date
    ).all()

    # Collect unavailable time slots
    unavailable_times = [
        TimeSlot(start_time=appointment.dateAppointment)
        for appointment in appointments
    ]

    return UnavailableTimesResponse(unavailable_times=unavailable_times)

@router.get("/verify-integrity/{consultation_id}")
async def verify_consultation_integrity(
    consultation_id: int,
    current_user: AuthUser = Depends(allow_patient),
    db: Session = Depends(get_db)):
    """
    Verifies consultation integrity by comparing database and blockchain data.
    """
    try:
        # Fetch consultation from database
        consultation = db.query(models.Consultation).filter(models.Consultation.id == consultation_id).first()
        if not consultation:
            raise HTTPException(status_code=404, detail="Consultation not found")

        # Check hypotheses
        hypotheses = consultation.hypotheses
        if not hypotheses:
            raise HTTPException(status_code=400, detail="No hypotheses found")

        # Fetch diagnosis from blockchain
        blockchain_diagnosis = get_diagnosis(consultation_id)

        # Compare data
        is_valid = (
            consultation.diagnosis == blockchain_diagnosis["doctor_diagnosis"] and
            consultation.patient_id == blockchain_diagnosis["patient_id"] and
            consultation.doctor_id == blockchain_diagnosis["doctor_id"]
        )

        # Compare hypotheses (up to 3)
        for i, hypo in enumerate(hypotheses[:3]):
            condition_field = f"condition{i+1}"
            confidence_field = f"confidence{i+1}"
            if (hypo.condition != blockchain_diagnosis[condition_field] or
                hypo.confidence != blockchain_diagnosis[confidence_field]):
                is_valid = False
                break

        return {
            "message": "Integrity verification completed",
            "consultation_id": consultation_id,
            "is_valid": is_valid
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify integrity: {str(e)}")