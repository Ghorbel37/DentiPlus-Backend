"""Main class containing endpoints
Main application entrypoint"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dependencies.database import engine
from dependencies.get_db import get_db
import models
import schemas
from services.llm import diagnose_patient_en,diagnose_patient_fr
from services.blockchain import get_value, set_value, get_accounts

# Enable SQLAlchemy logging: Shows SQL queries
#
# import logging
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","*"],  # Allow your React app's origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

@app.post("/patients/", response_model=schemas.Patient)
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    db_patient = models.Patient(name=patient.name, birthdate=patient.birthdate)
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

@app.get("/patients/{patient_id}", response_model=schemas.Patient)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@app.post("/diagnosis/", response_model=schemas.Diagnosis)
def create_diagnosis(diagnosis: schemas.DiagnosisCreate, db: Session = Depends(get_db)):
    # Check if the patient exists
    patient = db.query(models.Patient).filter(models.Patient.id == diagnosis.patientId).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Create the diagnosis
    db_diagnosis = models.Diagnosis(
        condition1=diagnosis.condition1,
        confidence1=diagnosis.confidence1,
        condition2=diagnosis.condition2,
        confidence2=diagnosis.confidence2,
        condition3=diagnosis.condition3,
        confidence3=diagnosis.confidence3,
        doctorDiagnosis=diagnosis.doctorDiagnosis,
        patientId=diagnosis.patientId
    )
    db.add(db_diagnosis)
    db.commit()
    db.refresh(db_diagnosis)
    return db_diagnosis

# Get diagnoses by patient name
@app.get("/diagnoses/", response_model=list[schemas.Diagnosis])
def get_diagnoses_by_patient_name(patient_name: str, db: Session = Depends(get_db)):
    # Find the patient by name
    patient = db.query(models.Patient).filter(models.Patient.name == patient_name).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Retrieve all diagnoses for the patient
    diagnoses = db.query(models.Diagnosis).filter(models.Diagnosis.patientId == patient.id).all()
    return diagnoses

@app.post("/diagnose-en")
def diagnose_en(request: schemas.SymptomRequest):
    return diagnose_patient_en(request.symptoms, request.additional_details)

@app.post("/diagnose-fr")
def diagnose_fr(request: schemas.SymptomRequest):
    return diagnose_patient_fr(request.symptoms, request.additional_details)

@app.get("/get-value")
async def get_value():
    return get_value()

@app.post("/set-value/{new_value}")
def set_value(new_value: int):
    return set_value(new_value)

@app.get("/accounts")
async def get_accounts():
    get_accounts()