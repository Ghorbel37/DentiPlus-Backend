from pydantic import BaseModel
from typing import Optional
from models import RoleUser

class User(BaseModel):
    id: int
    email: str
    role: RoleUser
    disabled: Optional[bool] = False

    class Config:
        from_attributes = True

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str