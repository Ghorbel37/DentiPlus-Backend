from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies.get_db import get_db
from dependencies.env import BCRYPT_SALT_ROUNDS
from dependencies.auth import bcrypt
import models
from schemas.patient_schemas import Patient, PatientCreate, PatientUpdate
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

    # Create Patient
    db_patient = models.Patient(
        calories=patient.calories,
        frequenceCardiaque=patient.frequenceCardiaque,
        poids=patient.poids
    )
    db_user.patient = db_patient  # Link Patient to User

    db.add(db_user)  # Adding User will cascade to Patient
    db.commit()  # Single commit for both
    db.refresh(db_user)  # Refresh User
    db.refresh(db_patient)  # Refresh Patient

    return {
        "id": db_patient.id,
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

@router.put("/{patient_id}", response_model=Patient)
def update_patient(patient_id: int, patient_update: PatientUpdate, db: Session = Depends(get_db)):
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    db_user = db_patient.user
    
    # Update User fields if provided
    if patient_update.email is not None:
        # Check if new email is already taken by another user
        if db.query(models.User).filter(models.User.email == patient_update.email, models.User.id != db_user.id).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        db_user.email = patient_update.email
    if patient_update.name is not None:
        db_user.name = patient_update.name
    if patient_update.adress is not None:
        db_user.adress = patient_update.adress
    if patient_update.birthdate is not None:
        db_user.birthdate = patient_update.birthdate
    if patient_update.phoneNumber is not None:
        db_user.phoneNumber = patient_update.phoneNumber
    
    # Update Patient fields if provided
    if patient_update.calories is not None:
        db_patient.calories = patient_update.calories
    if patient_update.frequenceCardiaque is not None:
        db_patient.frequenceCardiaque = patient_update.frequenceCardiaque
    if patient_update.poids is not None:
        db_patient.poids = patient_update.poids

    db.commit()
    db.refresh(db_user)
    db.refresh(db_patient)

    return {
        "id": db_patient.id,
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