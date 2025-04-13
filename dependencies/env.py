"""Load environement variables"""
import os
from dotenv import load_dotenv
from dependencies.get_ngrok_url import get_ngrok_url

load_dotenv(override=True)

# Github Gist Information
GIST_ID = os.getenv("GIST_ID")

# BASE_URL = os.getenv("BASE_URL")
BASE_URL = get_ngrok_url(GIST_ID)

DATABASE_URL = os.getenv("DATABASE_URL")
BLOCKCHAIN_URL = os.getenv("BLOCKCHAIN_URL")

# Contract details (replace with your deployed contract address)
STORAGE_CONTRACT_ADDRESS = os.getenv("STORAGE_CONTRACT_ADDRESS")
DIAGNOSIS_CONTRACT_ADDRESS = os.getenv("DIAGNOSIS_CONTRACT_ADDRESS")
# Public address
ACCOUNT = os.getenv("ACCOUNT")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "20"))

# OAuth2 Configuration
TOKEN_URL = os.getenv("TOKEN_URL", "auth/token")

# Bcrypt settings
BCRYPT_SALT_ROUNDS = int(os.getenv("BCRYPT_SALT_ROUNDS", "12"))

# Allowed roles (for role-based access control)
ROLES = {
    "DOCTOR": os.getenv("ROLE_DOCTOR", "doctor"),
    "PATIENT": os.getenv("ROLE_PATIENT", "patient")
}

# Function to get environment variables with optional default values
def get_env_var(name: str, default: str = None) -> str:
    return os.getenv(name, default)