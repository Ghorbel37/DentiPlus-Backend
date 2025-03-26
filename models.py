"""Contains SQLAlchemy database models inheriting from Base
Can be used to generate database"""
from sqlalchemy import Column, Integer, String, Date, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from dependencies.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    birthdate = Column(Date, nullable=True)

class Diagnosis(Base):
    __tablename__ = "diagnosis"

    id = Column(Integer, primary_key=True, index=True)
    condition1 = Column(String(255), nullable=False)
    confidence1 = Column(Integer, nullable=False)
    condition2 = Column(String(255), nullable=False)
    confidence2 = Column(Integer, nullable=False)
    condition3 = Column(String(255), nullable=False)
    confidence3 = Column(Integer, nullable=False)
    doctorDiagnosis = Column(String(255), nullable=True)
    date = Column(TIMESTAMP, server_default=func.now())
    patientId = Column(Integer, ForeignKey('patients.id'), nullable=False)
