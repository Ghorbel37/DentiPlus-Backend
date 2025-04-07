from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Enums
class RoleUser(str, Enum):
    DOCTOR = "DOCTOR"
    PATIENT = "PATIENT"

class EtatConsultation(str, Enum):
    VALIDE = "VALIDE"
    EN_ATTENTE = "EN_ATTENTE"
    RECONSULTATION = "RECONSULTATION"

class EtatAppointment(str, Enum):
    PLANIFIE = "PLANIFIE"
    COMPLETE = "COMPLETE"
    ANNULE = "ANNULE"

class MessageSenderType(str, Enum):
    SYSTEM = "SYSTEM"
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    DOCTOR = "DOCTOR"

# Base Schemas
class UserBase(BaseModel):
    adress: Optional[str] = None
    birthdate: Optional[datetime] = None
    email: str
    name: str
    phoneNumber: Optional[str] = None
    role: RoleUser

class DoctorBase(BaseModel):
    description: Optional[str] = None
    rating: Optional[float] = 0.0

class PatientBase(BaseModel):
    calories: Optional[int] = None
    frequenceCardiaque: Optional[int] = None
    poids: Optional[int] = None

class ChatMessageBase(BaseModel):
    content: str
    sender_type: MessageSenderType
    timestamp: Optional[datetime] = None

class HypotheseBase(BaseModel):
    condition: str
    confidence: int

class SymptomBase(BaseModel):
    symptom: str

# Response Schemas
class UserResponse(UserBase):
    id: int
    class Config:
        from_attributes = True

class DoctorResponse(DoctorBase):
    id: int
    user: UserResponse
    class Config:
        from_attributes = True

class PatientResponse(PatientBase):
    id: int
    user: UserResponse
    class Config:
        from_attributes = True

class ChatMessageResponse(ChatMessageBase):
    id: int
    consultation_id: int
    class Config:
        from_attributes = True

class HypotheseResponse(HypotheseBase):
    id: int
    consultation_id: int
    class Config:
        from_attributes = True

class SymptomRequest(BaseModel):
    symptoms: List[str]
    additional_details: str = "None"

class SymptomResponse(SymptomBase):
    id: int
    consultation_id: int
    class Config:
        from_attributes = True

class ConsultationBase(BaseModel):
    date: Optional[datetime] = None
    diagnostique: Optional[str] = None
    chat_summary: Optional[str] = None
    etat: EtatConsultation
    fraisAdministratives: Optional[float] = None
    prix: Optional[float] = None

class ConsultationResponse(ConsultationBase):
    id: int
    doctor: DoctorResponse
    patient: PatientResponse
    chat_messages: List[ChatMessageResponse] = []
    hypotheses: List[HypotheseResponse] = []
    symptoms: List[SymptomResponse] = []
    class Config:
        from_attributes = True

class ConsultationCreate(BaseModel):
    patient_id: int
    doctor_id: int
    etat: EtatConsultation = EtatConsultation.EN_ATTENTE

class ConversationHistoryCreate(BaseModel):
    consultation_id: int
    content: str
    sender_type: MessageSenderType