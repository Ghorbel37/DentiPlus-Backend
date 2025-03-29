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