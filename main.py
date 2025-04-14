from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dependencies.database import engine
import models
from controllers.llm_controller import router as llm_router
# from controllers.auth_controller import router as auth_router
from controllers import auth_controller, blockchain_consultation_controller, consultation_patient_controller, consultation_doctor_controller, user_controller, patient_controller, doctor_controller

# # Enable SQLAlchemy logging: Shows SQL queries
# import logging
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FastAPI Backend",
    description="Backend that manages DB, LLM and Blockchain.",
    version="1.0.0"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers from controllers
app.include_router(auth_controller.router)
# app.include_router(patient_router, prefix="/patients", tags=["Patients"])
# app.include_router(diagnosis_router, prefix="/diagnoses", tags=["Diagnoses"])
app.include_router(blockchain_consultation_controller.router)
app.include_router(llm_router, prefix="/llm", tags=["LLM"])
# app.include_router(diagnosis_router)
app.include_router(user_controller.router)
app.include_router(patient_controller.router)
app.include_router(doctor_controller.router)
app.include_router(consultation_patient_controller.router)
app.include_router(consultation_doctor_controller.router)