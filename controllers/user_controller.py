import os
import shutil
import bcrypt
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from dependencies.auth import bcrypt, get_current_active_user
from dependencies.env import BCRYPT_SALT_ROUNDS
from dependencies.get_db import get_db
import models
from schemas.auth_schemas import User as AuthUser
from schemas.user_schemas import User, UserListElement, UserUpdatePassword

router = APIRouter(prefix="/users", tags=["Users"])

# Directory to store profile photos
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.get("/", response_model=list[UserListElement])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return users

# New endpoint to get the current logged-in user
@router.get("/me", response_model=User)
async def get_current_user(
    current_user: AuthUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve the details of the currently authenticated user.
    
    Args:
        current_user: The authenticated user (via dependency).
        db: The database session (via dependency).
    
    Returns:
        The User object representing the current user.
    
    Raises:
        HTTPException: If the user is not found in the database.
    """
    # Fetch the user from the database using the authenticated user's email
    db_user = db.query(models.User).filter(models.User.email == current_user.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return db_user

@router.get("/{user_id}", response_model=User)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/name/{name}", response_model=list[User])
def get_users_by_name(name: str, db: Session = Depends(get_db)):
    users = db.query(models.User).filter(models.User.name.ilike(f"%{name}%")).all()
    if not users:
        raise HTTPException(status_code=404, detail="No users found with that name")
    return users

@router.put("/me/password", response_model=AuthUser)
def update_password(
    password_update: UserUpdatePassword,
    current_user: AuthUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Fetch the user from the database using the authenticated user's email
    db_user = db.query(models.User).filter(models.User.email == current_user.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify current password
    if not bcrypt.checkpw(password_update.current_password.encode(), db_user.password.encode()):
        raise HTTPException(status_code=401, detail="Incorrect current password")

    # Hash the new password
    new_hashed_password = bcrypt.hashpw(password_update.new_password.encode(), bcrypt.gensalt(BCRYPT_SALT_ROUNDS)).decode()
    
    # Update the password
    db_user.password = new_hashed_password
    db.commit()
    db.refresh(db_user)

    return {
        "email": db_user.email,
        "name": db_user.name,
        "role": db_user.role
    }

# New endpoint to upload profile photo
@router.post("/me/photo", response_model=User)
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: AuthUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload or update the profile photo for the current user.
    
    Args:
        file: The uploaded image file (e.g., JPEG, PNG).
        current_user: The authenticated user (via dependency).
        db: The database session (via dependency).
    
    Returns:
        The updated User object with the profile_photo path.
    
    Raises:
        HTTPException: If the user is not found or the file type is invalid.
    """
    # Validate file type
    allowed_extensions = {".jpg", ".jpeg", ".png"}
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only JPG, JPEG, and PNG are allowed."
        )

    # Fetch the user
    db_user = db.query(models.User).filter(models.User.email == current_user.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate unique file path (e.g., uploads/user_1_profile.jpg)
    file_name = f"user_{db_user.id}_profile{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    # Save the file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Update user's profile_photo path
    db_user.profile_photo = file_path
    db.commit()
    db.refresh(db_user)

    return db_user

# New endpoint to get profile photo
@router.get("/me/photo", response_class=FileResponse)
async def get_profile_photo(
    current_user: AuthUser = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve the profile photo for the current user.
    
    Args:
        current_user: The authenticated user (via dependency).
        db: The database session (via dependency).
    
    Returns:
        The image file as a FileResponse.
    
    Raises:
        HTTPException: If the user or photo is not found, or the file is invalid.
    """
    # Fetch the user
    db_user = db.query(models.User).filter(models.User.email == current_user.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if profile photo exists
    if not db_user.profile_photo or not os.path.exists(db_user.profile_photo):
        raise HTTPException(status_code=404, detail="Profile photo not found")

    return FileResponse(db_user.profile_photo)