"""Contains SQLAlchemy database models inheriting from Base
Can be used to generate database"""
from sqlalchemy import Boolean, Column, Integer, String, Float, Date, TIMESTAMP, ForeignKey, Enum, Table, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from dependencies.database import Base  # Adjust if needed
import enum

# Enum definitions
class RoleUser(enum.Enum):
    DOCTOR = "DOCTOR"
    PATIENT = "PATIENT"

class EtatConsultation(enum.Enum):
    VALIDE = "VALIDE"
    EN_ATTENTE = "EN_ATTENTE"
    RECONSULTATION = "RECONSULTATION"

class EtatAppointment(enum.Enum):
    PLANIFIE = "PLANIFIE"
    COMPLETE = "COMPLETE"
    ANNULE = "ANNULE"


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"mysql_engine": "InnoDB"}
    
    id = Column(Integer, primary_key=True, index=True)
    adress = Column(String(255), nullable=True)
    birthdate = Column(Date, nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    phoneNumber = Column(String(20), nullable=True)
    role = Column(Enum(RoleUser), nullable=False)
    disabled = Column(Boolean, default=False, nullable=False)

    # Relationships
    doctor = relationship("Doctor", back_populates="user", uselist=False, cascade="all, delete-orphan")
    patient = relationship("Patient", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Doctor(Base):
    __tablename__ = "doctors"
    __table_args__ = {"mysql_engine": "InnoDB"}
    
    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    description = Column(Text, nullable=True)
    rating = Column(Float, default=0.0)

    # Relationship
    user = relationship("User", back_populates="doctor")
    consultations = relationship("Consultation", back_populates="doctor", foreign_keys="Consultation.doctor_id")

class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = {"mysql_engine": "InnoDB"}
    
    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    calories = Column(Integer, nullable=True)
    frequenceCardiaque = Column(Integer, nullable=True)
    poids = Column(Integer, nullable=True)

    # Relationship
    user = relationship("User", back_populates="patient")
    consultations = relationship("Consultation", back_populates="patient", foreign_keys="Consultation.patient_id")

class Consultation(Base):
    __tablename__ = "consultations"
    __table_args__ = {"mysql_engine": "InnoDB"}
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    diagnosis = Column(String(255), nullable=True)
    chat_summary = Column(Text, nullable=True)
    doctor_note = Column(Text, nullable=True)
    etat = Column(Enum(EtatConsultation), nullable=False)
    fraisAdministratives = Column(Float, nullable=True)
    prix = Column(Float, nullable=True)
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)

    # Relationships
    doctor = relationship("Doctor", back_populates="consultations", foreign_keys=[doctor_id])
    patient = relationship("Patient", back_populates="consultations", foreign_keys=[patient_id])
    appointment = relationship("Appointment", back_populates="consultation", uselist=False, cascade="all, delete-orphan")
    hypotheses = relationship("Hypothese", back_populates="consultation", cascade="all, delete-orphan")
    symptoms = relationship("Symptoms", back_populates="consultation", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="consultation",cascade="all, delete-orphan",order_by="ChatMessage.timestamp")

class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = {"mysql_engine": "InnoDB"}
    
    id = Column(Integer, primary_key=True, index=True)
    dateCreation = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    dateAppointment = Column(TIMESTAMP, nullable=False)
    etat = Column(Enum(EtatAppointment), nullable=False)
    consultation_id = Column(Integer, ForeignKey('consultations.id'), nullable=False)

    # Relationship
    consultation = relationship("Consultation", back_populates="appointment")

class Hypothese(Base):
    __tablename__ = "hypotheses"
    __table_args__ = {"mysql_engine": "InnoDB"}
    
    id = Column(Integer, primary_key=True, index=True)
    condition = Column(String(255), nullable=False)
    confidence = Column(Integer, nullable=False)
    consultation_id = Column(Integer, ForeignKey('consultations.id'), nullable=False)

    # Relationship
    consultation = relationship("Consultation", back_populates="hypotheses")

class Symptoms(Base):
    __tablename__ = "symptoms"
    __table_args__ = {"mysql_engine": "InnoDB"}
    
    id = Column(Integer, primary_key=True, index=True)
    symptom = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    consultation_id = Column(Integer, ForeignKey('consultations.id'), nullable=False)  # New field

    # Relationships
    consultation = relationship("Consultation", back_populates="symptoms")

class MessageSenderType(enum.Enum):
    SYSTEM = "SYSTEM"
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    DOCTOR = "DOCTOR"  # For future use if doctors join chats

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = {"mysql_engine": "InnoDB"}
    
    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey('consultations.id'), nullable=False)
    content = Column(Text, nullable=False)  # Using Text instead of String for longer messages
    sender_type = Column(Enum(MessageSenderType), nullable=False)
    timestamp = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    
    # Relationship
    consultation = relationship("Consultation", back_populates="chat_messages")