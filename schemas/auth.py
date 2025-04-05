from pydantic import BaseModel
from typing import Optional

# Pydantic models
class User(BaseModel):
    email: str
    role: str
    disabled: Optional[bool] = False

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str