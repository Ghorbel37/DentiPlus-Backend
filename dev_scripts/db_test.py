"""Tests Database connection
Run with: python db_test"""
from sqlalchemy import create_engine
from dependencies.env import DATABASE_URL

SQLALCHEMY_DATABASE_URL = DATABASE_URL

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    conn = engine.connect()
    print("Database connected successfully!")
    conn.close()
except Exception as e:
    print("Database connection failed:", str(e))
