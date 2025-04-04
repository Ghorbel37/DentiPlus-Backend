"""Contains SQLAlchemy database models inheriting from Base
Can be used to generate database"""
from sqlalchemy import Column, Integer, String, Float, Date, TIMESTAMP, ForeignKey, Enum, Table
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
    PAYE = "PAYE"
    NON_PAYE = "NON_PAYE"

# Association table for many-to-many relationship between Consultation and Symptomes
consultation_symptomes = Table(
    'consultation_symptomes', Base.metadata,
    Column('consultation_id', Integer, ForeignKey('consultations.id'), primary_key=True),
    Column('symptome_id', Integer, ForeignKey('symptomes.id'), primary_key=True),
    mysql_engine="InnoDB"
)

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

    # Relationships
    doctors = relationship("Doctor", back_populates="user", cascade="all, delete-orphan")
    patients = relationship("Patient", back_populates="user", cascade="all, delete-orphan")
    symptomes = relationship("Symptomes", back_populates="user", cascade="all, delete-orphan")

class Doctor(Base):
    __tablename__ = "doctors"
    __table_args__ = {"mysql_engine": "InnoDB"}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Relationship
    user = relationship("User", back_populates="doctors")
    consultations = relationship("Consultation", back_populates="doctor", foreign_keys="Consultation.doctor_id")

class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = {"mysql_engine": "InnoDB"}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    calories = Column(Integer, nullable=True)
    frequenceCardiaque = Column(Integer, nullable=True)
    poids = Column(Integer, nullable=True)

    # Relationship
    user = relationship("User", back_populates="patients")
    consultations = relationship("Consultation", back_populates="patient", foreign_keys="Consultation.patient_id")

class Consultation(Base):
    __tablename__ = "consultations"
    __table_args__ = {"mysql_engine": "InnoDB"}
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    diagnostique = Column(String(255), nullable=True)
    doctorNote = Column(String(255), nullable=True)
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
    symptomes = relationship("Symptomes", secondary=consultation_symptomes, back_populates="consultations")

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

class Symptomes(Base):
    __tablename__ = "symptomes"
    __table_args__ = {"mysql_engine": "InnoDB"}
    
    id = Column(Integer, primary_key=True, index=True)
    symptome = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Relationships
    user = relationship("User", back_populates="symptomes")
    consultations = relationship("Consultation", secondary=consultation_symptomes, back_populates="symptomes")