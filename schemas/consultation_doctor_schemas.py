from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from models import EtatConsultation, MessageSenderType

class ChatMessage(BaseModel):
    id: int
    content: str
    sender_type: MessageSenderType
    timestamp: datetime

    class Config:
        from_attributes = True

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

class DoctorNoteUpdate(BaseModel):
    doctor_note: str