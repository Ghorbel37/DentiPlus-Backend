# dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
import bcrypt
from typing import Optional
from datetime import datetime, timedelta
from dependencies.env import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, TOKEN_URL, BCRYPT_SALT_ROUNDS
from sqlalchemy.orm import Session
from dependencies.get_db import get_db
import models
from schemas.auth_schemas import UserInDB, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=TOKEN_URL)

# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def get_user(db: Session, email: str) -> Optional[UserInDB]:
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        return UserInDB(
            email=user.email,
            role=user.role.value,
            hashed_password=user.password,
            disabled=False  # Add a disabled field to models.User if needed
        )
    return None

def authenticate_user(db: Session, email: str, password: str) -> Optional[UserInDB]:
    user = get_user(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = get_user(db, email)
    if user is None or user.disabled:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Role checker
class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    async def __call__(self, user: User = Depends(get_current_active_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )
        return user