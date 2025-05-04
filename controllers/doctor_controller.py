from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from controllers.consultation_patient_controller import AuthUser
from dependencies.get_db import get_db
from dependencies.env import BCRYPT_SALT_ROUNDS
from dependencies.auth import RoleChecker, bcrypt
import models
from schemas.doctor_schemas import Doctor, DoctorCreate, DoctorUpdate
from models import RoleUser

router = APIRouter(prefix="/doctors", tags=["Doctors"])

# Dependency to ensure the user is authenticated
allow_both = RoleChecker([models.RoleUser.PATIENT, models.RoleUser.DOCTOR])

@router.get("/single-doctor", response_model=Doctor)
def get_single_doctor_endpoint(
    current_user: AuthUser = Depends(allow_both),
    db: Session = Depends(get_db)
):
    doctor = db.query(models.Doctor).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="No doctor found in the system")
    
    user = doctor.user
    
    return {
        "id": doctor.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "adress": user.adress,
        "birthdate": user.birthdate,
        "phoneNumber": user.phoneNumber,
        "description": doctor.description,
        "rating": doctor.rating
    }

@router.post("/single-doctor", response_model=Doctor)
async def create_single_doctor(doctor: DoctorCreate, db: Session = Depends(get_db)):
    # Check if any doctor already exists
    if db.query(models.Doctor).first():
        raise HTTPException(status_code=400, detail="A doctor already exists in the system")

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

    # Create Doctor
    db_doctor = models.Doctor(
        description=doctor.description,
        rating=doctor.rating
    )

    db_user.doctor = db_doctor
    db.add(db_user)
    
    try:
        db.commit()
        db.refresh(db_user)
        db.refresh(db_doctor)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Construct response
    return {
        "id": db_doctor.id,
        "email": db_user.email,
        "name": db_user.name,
        "role": db_user.role,
        "adress": db_user.adress,
        "birthdate": db_user.birthdate,
        "phoneNumber": db_user.phoneNumber,
        "description": db_doctor.description,
        "rating": db_doctor.rating
    }

# @router.post("/", response_model=Doctor)
# def create_doctor(doctor: DoctorCreate, db: Session = Depends(get_db)):
#     # Check if email already exists
#     if db.query(models.User).filter(models.User.email == doctor.email).first():
#         raise HTTPException(status_code=400, detail="Email already registered")

#     # Hash the password
#     hashed_password = bcrypt.hashpw(doctor.password.encode(), bcrypt.gensalt(BCRYPT_SALT_ROUNDS)).decode()

#     # Create User
#     db_user = models.User(
#         email=doctor.email,
#         adress=doctor.adress,
#         birthdate=doctor.birthdate,
#         name=doctor.name,
#         password=hashed_password,
#         phoneNumber=doctor.phoneNumber,
#         role=RoleUser.DOCTOR
#     )

#     # Create Doctor
#     db_doctor = models.Doctor(
#         description=doctor.description,
#         rating=doctor.rating
#     )

#     db_user.doctor = db_doctor
#     db.add(db_user)
    
#     try:
#         db.commit()
#         db.refresh(db_user)
#         db.refresh(db_doctor)
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

#     # Construct response
#     return {
#         "id": db_doctor.id,
#         "email": db_user.email,
#         "name": db_user.name,
#         "role": db_user.role,
#         "adress": db_user.adress,
#         "birthdate": db_user.birthdate,
#         "phoneNumber": db_user.phoneNumber,
#         "description": db_doctor.description,
#         "rating": db_doctor.rating
#     }

@router.get("/{doctor_id}", response_model=Doctor)
def get_doctor_by_id(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Fetch associated user
    user = doctor.user
    
    return {
        "id": doctor.id,
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
        "email": doctor.user.email,
        "name": doctor.user.name,
        "role": doctor.user.role,
        "adress": doctor.user.adress,
        "birthdate": doctor.user.birthdate,
        "phoneNumber": doctor.user.phoneNumber,
        "description": doctor.description,
        "rating": doctor.rating
    } for doctor in doctors]

@router.put("/{doctor_id}", response_model=Doctor)
def update_doctor(doctor_id: int, doctor_update: DoctorUpdate, db: Session = Depends(get_db)):
    db_doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if db_doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    db_user = db_doctor.user
    
    # Update User fields if provided
    if doctor_update.email is not None:
        # Check if new email is already taken by another user
        if db.query(models.User).filter(models.User.email == doctor_update.email, models.User.id != db_user.id).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        db_user.email = doctor_update.email
    if doctor_update.name is not None:
        db_user.name = doctor_update.name
    if doctor_update.adress is not None:
        db_user.adress = doctor_update.adress
    if doctor_update.birthdate is not None:
        db_user.birthdate = doctor_update.birthdate
    if doctor_update.phoneNumber is not None:
        db_user.phoneNumber = doctor_update.phoneNumber
    
    # Update Doctor fields if provided
    if doctor_update.description is not None:
        db_doctor.description = doctor_update.description
    if doctor_update.rating is not None:
        db_doctor.rating = doctor_update.rating

    db.commit()
    db.refresh(db_user)
    db.refresh(db_doctor)

    return {
        "id": db_doctor.id,
        "email": db_user.email,
        "name": db_user.name,
        "role": db_user.role,
        "adress": db_user.adress,
        "birthdate": db_user.birthdate,
        "phoneNumber": db_user.phoneNumber,
        "description": db_doctor.description,
        "rating": db_doctor.rating
    }