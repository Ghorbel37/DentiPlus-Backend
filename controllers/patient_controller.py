from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies.get_db import get_db
from dependencies.env import BCRYPT_SALT_ROUNDS
from dependencies.auth import bcrypt
import models
from schemas.patient_schemas import Patient, PatientCreate
from models import RoleUser

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.post("/", response_model=Patient)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    if db.query(models.User).filter(models.User.email == patient.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password
    hashed_password = bcrypt.hashpw(patient.password.encode(), bcrypt.gensalt(BCRYPT_SALT_ROUNDS)).decode()

    # Create User
    db_user = models.User(
        email=patient.email,
        adress=patient.adress,
        birthdate=patient.birthdate,
        name=patient.name,
        password=hashed_password,
        phoneNumber=patient.phoneNumber,
        role=RoleUser.PATIENT
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create Patient
    db_patient = models.Patient(
        user_id=db_user.id,
        calories=patient.calories,
        frequenceCardiaque=patient.frequenceCardiaque,
        poids=patient.poids
    )
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)

    return {
        "id": db_patient.id,
        "user_id": db_user.id,
        "email": db_user.email,
        "name": db_user.name,
        "role": db_user.role,
        "adress": db_user.adress,
        "birthdate": db_user.birthdate,
        "phoneNumber": db_user.phoneNumber,
        "calories": db_patient.calories,
        "frequenceCardiaque": db_patient.frequenceCardiaque,
        "poids": db_patient.poids
    }

@router.get("/{patient_id}", response_model=Patient)
def get_patient_by_id(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Fetch associated user
    user = patient.user
    
    return {
        "id": patient.id,
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "adress": user.adress,
        "birthdate": user.birthdate,
        "phoneNumber": user.phoneNumber,
        "calories": patient.calories,
        "frequenceCardiaque": patient.frequenceCardiaque,
        "poids": patient.poids
    }

@router.get("/name/{name}", response_model=list[Patient])
def get_patients_by_name(name: str, db: Session = Depends(get_db)):
    patients = db.query(models.Patient).join(models.User).filter(models.User.name.ilike(f"%{name}%")).all()
    if not patients:
        raise HTTPException(status_code=404, detail="No patients found with that name")
    return [{
        "id": patient.id,
        "user_id": patient.user.id,
        "email": patient.user.email,
        "name": patient.user.name,
        "role": patient.user.role,
        "adress": patient.user.adress,
        "birthdate": patient.user.birthdate,
        "phoneNumber": patient.user.phoneNumber,
        "calories": patient.calories,
        "frequenceCardiaque": patient.frequenceCardiaque,
        "poids": patient.poids
    } for patient in patients]