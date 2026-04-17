import os
import random
import string
from datetime import datetime, timedelta
from typing import Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.models.user import User, Degree, TestScore
from app.schemas.user import UserCreate, UserResponse, Token, DegreeCreate, TestScoreCreate
from app.api.deps import get_current_user
from app.services.notification import notification_service

router = APIRouter()

# ── OTP helpers ────────────────────────────────────────────────────────────────

def generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))

# ── Schemas ────────────────────────────────────────────────────────────────────

class OTPRequest(BaseModel):
    email: EmailStr

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

class OTPVerifyResponse(BaseModel):
    access_token: str
    token_type: str

class UserUpdate(BaseModel):
    password: Optional[str] = None
    budget: Optional[int] = None
    target_countries: Optional[List[str]] = None
    work_experience_years: Optional[int] = None
    preferred_intake: Optional[str] = None
    career_goal: Optional[str] = None
    preferred_environment: Optional[str] = None
    study_priority: Optional[str] = None
    learning_style: Optional[str] = None
    living_preference: Optional[str] = None
    
    # Nested Collections
    degrees: Optional[List[DegreeCreate]] = None
    tests: Optional[List[TestScoreCreate]] = None

# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> Any:
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing and existing.is_verified:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    
    otp = generate_otp()
    expires = datetime.utcnow() + timedelta(minutes=10)

    # Base user data
    user_data = {
        "hashed_password": get_password_hash(user_in.password),
        "budget": user_in.budget,
        "target_countries": user_in.target_countries,
        "work_experience_years": user_in.work_experience_years,
        "preferred_intake": user_in.preferred_intake,
        "career_goal": user_in.career_goal,
        "preferred_environment": user_in.preferred_environment,
        "study_priority": user_in.study_priority,
        "learning_style": user_in.learning_style,
        "living_preference": user_in.living_preference,
        "otp": otp,
        "otp_expires_at": expires,
        "is_verified": False
    }

    if existing:
        # Update existing unverified user
        for key, value in user_data.items():
            setattr(existing, key, value)
        
        # Clear old degrees/tests for this unverified user
        db.query(Degree).filter(Degree.user_id == existing.id).delete()
        db.query(TestScore).filter(TestScore.user_id == existing.id).delete()
        user = existing
    else:
        # Create new user
        user = User(email=user_in.email, **user_data)
        db.add(user)
        db.flush() # Get user.id

    # Add new degrees
    for d_in in user_in.degrees:
        db.add(Degree(user_id=user.id, **d_in.dict()))
    
    # Add new tests
    for t_in in user_in.tests:
        db.add(TestScore(user_id=user.id, **t_in.dict()))

    db.commit()
    background_tasks.add_task(notification_service.send_otp_email, user_in.email, otp)
    return {"email": user_in.email, "message": "OTP sent to your email. Please verify to activate your account."}

@router.post("/send-otp", response_model=dict)
def send_otp(req: OTPRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> Any:
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this email.")
    
    otp = generate_otp()
    user.otp = otp
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
    db.commit()
    
    background_tasks.add_task(notification_service.send_otp_email, user.email, otp)
    return {"message": "OTP sent to your email."}


@router.post("/verify-otp", response_model=OTPVerifyResponse)
def verify_otp(req: OTPVerifyRequest, db: Session = Depends(get_db)) -> Any:
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if not user.otp or user.otp != req.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP.")
    if user.otp_expires_at and datetime.utcnow() > user.otp_expires_at:
        raise HTTPException(status_code=400, detail="OTP has expired. Request a new one.")
    
    user.is_verified = True
    user.otp = None
    user.otp_expires_at = None
    db.commit()

    token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password.")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before logging in.")
    
    token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_user_me(current_user: User = Depends(get_current_user)) -> Any:
    return current_user

@router.patch("/me", response_model=UserResponse)
def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    data = user_update.dict(exclude_unset=True)
    if "password" in data:
        current_user.hashed_password = get_password_hash(data.pop("password"))
    
    # Handle nested degrees (Clear and Replace)
    if "degrees" in data:
        new_degrees = data.pop("degrees")
        db.query(Degree).filter(Degree.user_id == current_user.id).delete()
        for d_in in new_degrees:
            # d_in is a dict because of .dict() on user_update
            db.add(Degree(user_id=current_user.id, **d_in))
            
    # Handle nested tests (Clear and Replace)
    if "tests" in data:
        new_tests = data.pop("tests")
        db.query(TestScore).filter(TestScore.user_id == current_user.id).delete()
        for t_in in new_tests:
            db.add(TestScore(user_id=current_user.id, **t_in))

    for key, value in data.items():
        setattr(current_user, key, value)
    
    db.commit()
    db.refresh(current_user)
    return current_user
