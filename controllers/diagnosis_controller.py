from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies.get_db import get_db
import models
from schemas.diagnosis import Diagnosis, DiagnosisCreate

router = APIRouter()

@router.post("/", response_model=Diagnosis)
def create_diagnosis(diagnosis: DiagnosisCreate, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == diagnosis.patientId).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

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

@router.get("/", response_model=list[Diagnosis])
def get_diagnoses_by_patient_name(patient_name: str, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.name == patient_name).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    diagnoses = db.query(models.Diagnosis).filter(models.Diagnosis.patientId == patient.id).all()
    return diagnoses