from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List
from models import EtatConsultation, EtatAppointment, MessageSenderType

class ChatMessageCreate(BaseModel):
    content: str

class ChatMessage(BaseModel):
    id: int
    content: str
    sender_type: MessageSenderType
    timestamp: datetime

    class Config:
        from_attributes = True

class ConsultationCreate(BaseModel):
    diagnosis: Optional[str] = None
    chat_summary: Optional[str] = None
    doctor_note: Optional[str] = None
    fraisAdministratives: Optional[float] = None
    prix: Optional[float] = None

class Consultation(BaseModel):
    id: int
    date: datetime
    diagnosis: Optional[str] = None
    chat_summary: Optional[str] = None
    doctor_note: Optional[str] = None
    etat: EtatConsultation
    fraisAdministratives: Optional[float] = None
    prix: Optional[float] = None
    doctor_id: int
    patient_id: int
    chat_messages: List[ChatMessage] = []

    class Config:
        from_attributes = True

class ConsultationListElement(BaseModel):
    id: int
    date: datetime
    diagnosis: Optional[str] = None
    chat_summary: Optional[str] = None
    doctor_note: Optional[str] = None
    etat: EtatConsultation
    fraisAdministratives: Optional[float] = None
    prix: Optional[float] = None
    doctor_id: int
    patient_id: int

    class Config:
        from_attributes = True

# Appointment schemas
class AppointmentCreate(BaseModel):
    dateAppointment: datetime

class Appointment(BaseModel):
    id: int
    dateCreation: datetime
    dateAppointment: datetime
    etat: EtatAppointment
    consultation_id: int

    class Config:
        from_attributes = True

# New schemas for unavailable times
class UnavailableTimesRequest(BaseModel):
    date: date

class TimeSlot(BaseModel):
    start_time: datetime

class UnavailableTimesResponse(BaseModel):
    unavailable_times: List[TimeSlot]