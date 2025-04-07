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

class Doctor(DoctorBase):
    id: int
    user_id: int
    role: RoleUser = RoleUser.DOCTOR
    adress: Optional[str] = None
    birthdate: Optional[date] = None
    phoneNumber: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[float] = 0.0
    
    class Config:
        from_attributes = True