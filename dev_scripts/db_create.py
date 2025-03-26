"""Creates Database
Run with: python -m dev_scripts.db_create"""
from dependencies.database import engine
import models

models.Base.metadata.create_all(engine)

print("Database and tables created successfully!")
