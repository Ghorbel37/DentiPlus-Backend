from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from dependencies.get_db import get_db
from dependencies.auth import create_access_token, User as AuthUser, Token, bcrypt, BCRYPT_SALT_ROUNDS, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_active_user
from datetime import timedelta
import models
import schemas

router = APIRouter(prefix="/users", tags=["users"])

# Create a Patient account
@router.post("/patients/", response_model=schemas.Patient)
def create_patient(patient: schemas.PatientAccountCreate, db: Session = Depends(get_db)):
    # Check if username already exists
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
        role=patient.role
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
        
    # Construct the response according to the Patient schema
    response_data = {
        "id": db_user.id,
        "email": db_user.email,
        "adress": db_user.adress,
        "birthdate": db_user.birthdate,
        "name": db_user.name,
        "phoneNumber": db_user.phoneNumber,
        "role": db_user.role,
        "calories": db_patient.calories,
        "frequenceCardiaque": db_patient.frequenceCardiaque,
        "poids": db_patient.poids
    }
    return response_data

# Create a Doctor account
@router.post("/doctors/", response_model=schemas.Doctor)
def create_doctor(doctor: schemas.DoctorAccountCreate, db: Session = Depends(get_db)):
    # Check if username already exists
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
        role=doctor.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create Doctor
    db_doctor = models.Doctor(user_id=db_user.id)
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)

    response_data = {
        "id": db_user.id,
        "email": db_user.email,
        "adress": db_user.adress,
        "birthdate": db_user.birthdate,
        "name": db_user.name,
        "phoneNumber": db_user.phoneNumber,
        "role": db_user.role
        # Doctor fields would be included here if there were any
    }
    return response_data

# Optional: Create account and return token (combines creation with login)
@router.post("/accounts/token", response_model=Token)
def create_account_with_token(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if username already exists
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password
    hashed_password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt(BCRYPT_SALT_ROUNDS)).decode()

    # Create User
    db_user = models.User(
        email=user.email,
        adress=user.adress,
        birthdate=user.birthdate,
        name=user.name,
        password=hashed_password,
        phoneNumber=user.phoneNumber,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create Patient or Doctor based on role
    if user.role == schemas.RoleUser.PATIENT:
        db_patient = models.Patient(user_id=db_user.id)
        db.add(db_patient)
        db.commit()
    elif user.role == schemas.RoleUser.DOCTOR:
        db_doctor = models.Doctor(user_id=db_user.id)
        db.add(db_doctor)
        db.commit()
    else:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid role")

    # Generate token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email, "role": db_user.role.value},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Get current user (for testing, reusing your auth dependency)
@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: AuthUser = Depends(get_current_active_user), db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == current_user.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found in database")
    return db_user