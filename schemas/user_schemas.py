from datetime import date
from typing import Optional
from enum import Enum
from pydantic import BaseModel

# Enum for role validation (matches your ROLE_USER enum)
class RoleUser(str, Enum):
    DOCTOR = "DOCTOR"
    PATIENT = "PATIENT"

# Base schema for User
class UserBase(BaseModel):
    email: str
    adress: Optional[str] = None
    birthdate: Optional[date] = None
    name: str
    password: str
    phoneNumber: Optional[str] = None
    role: RoleUser

# Schema for creating a User
class UserCreate(UserBase):
    pass

# Schema for User response
class User(BaseModel):
    id: int
    email: str
    adress: Optional[str] = None
    birthdate: Optional[date] = None
    name: str
    phoneNumber: Optional[str] = None
    role: RoleUser

    class Config:
        from_attributes = True

# Schema for Doctor-specific fields (extensible)
class DoctorCreate(BaseModel):
    pass

class DoctorAccountCreate(UserCreate, DoctorCreate):
    role: RoleUser = RoleUser.DOCTOR

class Doctor(User, DoctorCreate):
    class Config:
        from_attributes = True