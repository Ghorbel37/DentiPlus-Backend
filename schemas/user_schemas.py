from pydantic import BaseModel
from datetime import date
from typing import Optional
from models import RoleUser

class UserBase(BaseModel):
    email: str
    name: str
    role: RoleUser

class UserCreate(UserBase):
    # password: str
    adress: Optional[str] = None
    birthdate: Optional[date] = None
    phoneNumber: Optional[str] = None

class UserUpdatePassword(BaseModel):
    current_password: str
    new_password: str

class UserListElement(UserBase):
    id: int
    
    class Config:
        from_attributes = True

class User(UserCreate):
    id: int
    
    class Config:
        from_attributes = True