"""Load environement variables"""
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
DATABASE_URL = os.getenv("DATABASE_URL")
BLOCKCHAIN_URL = os.getenv("BLOCKCHAIN_URL")

# Contract details (replace with your deployed contract address)
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
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
    "ADMIN": os.getenv("ROLE_ADMIN", "admin"),
    "USER": os.getenv("ROLE_USER", "user")
}

# Function to get environment variables with optional default values
def get_env_var(name: str, default: str = None) -> str:
    return os.getenv(name, default)