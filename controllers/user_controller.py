import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies.auth import bcrypt, get_current_active_user
from dependencies.env import BCRYPT_SALT_ROUNDS
from dependencies.get_db import get_db
import models
from schemas.auth_schemas import User as AuthUser
from schemas.user_schemas import User, UserListElement, UserUpdatePassword

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=list[UserListElement])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return users

@router.get("/{user_id}", response_model=User)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/name/{name}", response_model=list[User])
def get_users_by_name(name: str, db: Session = Depends(get_db)):
    users = db.query(models.User).filter(models.User.name.ilike(f"%{name}%")).all()
    if not users:
        raise HTTPException(status_code=404, detail="No users found with that name")
    return users

@router.put("/me/password", response_model=AuthUser)
def update_password(
    password_update: UserUpdatePassword,
    current_user: AuthUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Fetch the user from the database using the authenticated user's email
    db_user = db.query(models.User).filter(models.User.email == current_user.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify current password
    if not bcrypt.checkpw(password_update.current_password.encode(), db_user.password.encode()):
        raise HTTPException(status_code=401, detail="Incorrect current password")

    # Hash the new password
    new_hashed_password = bcrypt.hashpw(password_update.new_password.encode(), bcrypt.gensalt(BCRYPT_SALT_ROUNDS)).decode()
    
    # Update the password
    db_user.password = new_hashed_password
    db.commit()
    db.refresh(db_user)

    return {
        "email": db_user.email,
        "name": db_user.name,
        "role": db_user.role
    }