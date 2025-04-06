# DentiPlus Backend

**FastAPI-powered backend** for DentiPlus 🦷

## 🚀 Features
- **JWT Authentication** – Secure user access
- **Async Endpoints** – High-performance non-blocking operations
- **MySQL + SQLAlchemy** – Robust database management
- **Blockchain Integration** – Smart contract interactions
- **LLM Model Queries** – Connects to an external AI service

## ⚙️ Installation

### Prerequisites
- Python 3.9+
- MySQL server
- Blockchain node (if applicable)

### Steps
1. **Clone the repo**:
   ```bash
   git clone https://github.com/Ghorbel37/DentiPlus-Backend.git
   cd dentiplus-backend
2. **Rename the template file and update variables**:
   ```bash
   mv .env_template .env
3. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```
4. **Install dependencies**:
   ```python
   pip install -r requirements.txt

## 🚀 Running DentiPlus Backend


### Option A: Uvicorn
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### Option B: FastAPI CLI
   ```bash
   fastapi dev main.py --port 8000
   ```

Once the server is running, you can try all endpoins interactively at: **http://localhost:8000/docs**