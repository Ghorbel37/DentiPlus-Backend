from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies.get_db import get_db
from dependencies.env import BCRYPT_SALT_ROUNDS
from dependencies.auth import bcrypt
import models
from schemas.doctor_schemas import Doctor, DoctorCreate
from models import RoleUser

router = APIRouter(prefix="/doctors", tags=["Doctors"])

@router.post("/", response_model=Doctor)
def create_doctor(doctor: DoctorCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    if db.query(models.User).filter(models.User.email == doctor.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password
    hashed_password = bcrypt.hashpw(doctor.password.encode(), bcrypt.gensalt(BCRYPT_SALT_ROUNDS)).decode()

    # Create User
    db_user = models.User(
        email=doctor.email,
        adress=doctor.adress,
        birthdate=doctor.birthdate,
        name=doctor.name,
        password=hashed_password,
        phoneNumber=doctor.phoneNumber,
        role=RoleUser.DOCTOR
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create Doctor
    db_doctor = models.Doctor(
        user_id=db_user.id,
        description=doctor.description,
        rating=doctor.rating
    )
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)

    # Construct response
    return {
        "id": db_doctor.id,
        "user_id": db_user.id,
        "email": db_user.email,
        "name": db_user.name,
        "role": db_user.role,
        "adress": db_user.adress,
        "birthdate": db_user.birthdate,
        "phoneNumber": db_user.phoneNumber,
        "description": db_doctor.description,
        "rating": db_doctor.rating
    }

@router.get("/{doctor_id}", response_model=Doctor)
def get_doctor_by_id(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Fetch associated user
    user = doctor.user
    
    return {
        "id": doctor.id,
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "adress": user.adress,
        "birthdate": user.birthdate,
        "phoneNumber": user.phoneNumber,
        "description": doctor.description,
        "rating": doctor.rating
    }

@router.get("/name/{name}", response_model=list[Doctor])
def get_doctors_by_name(name: str, db: Session = Depends(get_db)):
    doctors = db.query(models.Doctor).join(models.User).filter(models.User.name.ilike(f"%{name}%")).all()
    if not doctors:
        raise HTTPException(status_code=404, detail="No doctors found with that name")
    
    return [{
        "id": doctor.id,
        "user_id": doctor.user.id,
        "email": doctor.user.email,
        "name": doctor.user.name,
        "role": doctor.user.role,
        "adress": doctor.user.adress,
        "birthdate": doctor.user.birthdate,
        "phoneNumber": doctor.user.phoneNumber,
        "description": doctor.description,
        "rating": doctor.rating
    } for doctor in doctors]