from datetime import date
from typing import Optional
from pydantic import BaseModel
from .user_schemas import RoleUser, User, UserCreate

class PatientBase(BaseModel):
    name: str
    birthdate: Optional[date] = None

# Schema for Patient-specific fields
class PatientCreate(BaseModel):
    calories: Optional[int] = None
    frequenceCardiaque: Optional[int] = None
    poids: Optional[int] = None

# Combined schemas for Patient and Doctor account creation
class PatientAccountCreate(UserCreate, PatientCreate):
    role: RoleUser = RoleUser.PATIENT

# Response schemas
class Patient(User, PatientCreate):
    class Config:
        from_attributes = True