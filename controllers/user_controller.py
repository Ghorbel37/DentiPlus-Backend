from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies.get_db import get_db
import models
from schemas.user_schemas import User, UserListElement

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