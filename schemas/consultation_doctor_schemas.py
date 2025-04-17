from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List
from models import EtatConsultation, MessageSenderType, RoleUser

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

class PatientInfo(BaseModel):
    id: int
    name: str =None
    email: str =None
    adress: Optional[str] = None
    birthdate: Optional[date] = None
    phoneNumber: Optional[str] = None
    calories: Optional[int] = None
    frequenceCardiaque: Optional[int] = None
    poids: Optional[int] = None

    class Config:
        from_attributes = True

class Symptom(BaseModel):
    symptom: str

    class Config:
        from_attributes = True

class Hypothese(BaseModel):
    condition: str
    confidence: int

    class Config:
        from_attributes = True

class ConsultationDetailed(BaseModel):
    id: int
    date: datetime
    diagnosis: Optional[str] = None
    chat_summary: Optional[str] = None
    doctor_note: Optional[str] = None
    etat: EtatConsultation
    fraisAdministratives: Optional[float] = None
    prix: Optional[float] = None
    patient: PatientInfo
    symptoms: List[Symptom] = []
    hypotheses: List[Hypothese] = []
    chat_messages: List[ChatMessage] = []

    class Config:
        from_attributes = True