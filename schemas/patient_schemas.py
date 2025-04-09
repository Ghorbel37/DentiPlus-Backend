from pydantic import BaseModel
from typing import Optional
from datetime import date
from models import RoleUser

class PatientBase(BaseModel):
    email: str
    name: str

class PatientCreateBase(BaseModel):
    email: str
    name: str
    password: str

class PatientCreate(PatientCreateBase):
    adress: Optional[str] = None
    birthdate: Optional[date] = None
    phoneNumber: Optional[str] = None
    calories: Optional[int] = None
    frequenceCardiaque: Optional[int] = None
    poids: Optional[int] = None

    class Config:
        from_attributes = True

class PatientUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    adress: Optional[str] = None
    birthdate: Optional[date] = None
    phoneNumber: Optional[str] = None
    calories: Optional[int] = None
    frequenceCardiaque: Optional[int] = None
    poids: Optional[int] = None

    class Config:
        from_attributes = True

class Patient(PatientBase):
    id: int
    role: RoleUser = RoleUser.PATIENT
    adress: Optional[str] = None
    birthdate: Optional[date] = None
    phoneNumber: Optional[str] = None
    calories: Optional[int] = None
    frequenceCardiaque: Optional[int] = None
    poids: Optional[int] = None

    class Config:
        from_attributes = True