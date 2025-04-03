from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies.get_db import get_db
import models
import schemas

router = APIRouter()

@router.post("/", response_model=schemas.Patient)
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    db_patient = models.Patient(name=patient.name, birthdate=patient.birthdate)
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

@router.get("/{patient_id}", response_model=schemas.Patient)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient