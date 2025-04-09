from pydantic import BaseModel
from typing import Optional
from datetime import date
from models import RoleUser

class DoctorBase(BaseModel):
    email: str
    name: str

class DoctorCreateBase(BaseModel):
    email: str
    name: str
    password: str

class DoctorCreate(DoctorCreateBase):
    adress: Optional[str] = None
    birthdate: Optional[date] = None
    phoneNumber: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[float] = 0.0

    class Config:
        from_attributes = True

class DoctorUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    adress: Optional[str] = None
    birthdate: Optional[date] = None
    phoneNumber: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[float] = None

    class Config:
        from_attributes = True

class Doctor(DoctorBase):
    id: int
    role: RoleUser = RoleUser.DOCTOR
    adress: Optional[str] = None
    birthdate: Optional[date] = None
    phoneNumber: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[float] = 0.0
    
    class Config:
        from_attributes = True