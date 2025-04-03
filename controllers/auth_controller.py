# controllers/auth_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from dependencies.auth import RoleChecker, authenticate_user, create_access_token,get_current_active_user, User, Token, fake_users_db
from dependencies.env import ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.get("/admin/data", dependencies=[Depends(RoleChecker(allowed_roles=["doctor"]))])
async def admin_data():
    return {"message": "This is admin-only data"}

@router.get("/user/data", dependencies=[Depends(RoleChecker(allowed_roles=["doctor", "patient"]))])
async def user_data():
    return {"message": "This is user or admin accessible data"}