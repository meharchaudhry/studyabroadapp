import os
import random
import string
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token
from app.api.deps import get_current_user

router = APIRouter()

# ── OTP helpers ────────────────────────────────────────────────────────────────

def generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))

def send_otp_email(email: str, otp: str):
    """
    Send OTP via SMTP if credentials are available, otherwise log to console.
    Set EMAIL_USER and EMAIL_PASSWORD env vars (Gmail App Password) to enable real emails.
    """
    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_PASSWORD")

    if email_user and email_pass:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Your StudyPathway Verification Code"
        msg["From"] = email_user
        msg["To"] = email

        html = f"""
        <html><body style="font-family:Inter,sans-serif;background:#f7f8fc;padding:40px;">
          <div style="max-width:480px;margin:auto;background:#fff;border-radius:16px;padding:40px;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
            <h2 style="color:#7C6FF7;margin-bottom:8px;">StudyPathway</h2>
            <p style="color:#5A6275;">Your verification code is:</p>
            <div style="font-size:48px;font-weight:700;letter-spacing:12px;color:#1A1D2E;text-align:center;margin:24px 0;">{otp}</div>
            <p style="color:#8B95A8;font-size:13px;">This code expires in 10 minutes. Do not share it.</p>
          </div>
        </body></html>
        """
        msg.attach(MIMEText(html, "html"))
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(email_user, email_pass)
                server.sendmail(email_user, email, msg.as_string())
            print(f"✅ OTP email sent to {email}")
        except Exception as e:
            print(f"⚠️  Email send failed: {e} — OTP for {email}: {otp}")
    else:
        print(f"📧 [MOCK EMAIL] OTP for {email}: {otp}  (set EMAIL_USER + EMAIL_PASSWORD to send real emails)")

# ── Schemas ────────────────────────────────────────────────────────────────────

class OTPRequest(BaseModel):
    email: EmailStr

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

class OTPVerifyResponse(BaseModel):
    access_token: str
    token_type: str

# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> Any:
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing and existing.is_verified:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    
    otp = generate_otp()
    expires = datetime.utcnow() + timedelta(minutes=10)

    # Convert INR budget to USD (1 USD ≈ 83 INR)
    budget_usd = user_in.budget
    if user_in.budget_inr and not budget_usd:
        budget_usd = int(user_in.budget_inr / 83)

    profile_fields = dict(
        full_name=user_in.full_name,
        cgpa=user_in.cgpa,
        budget=budget_usd,
        budget_inr=user_in.budget_inr,
        target_countries=user_in.target_countries,
        field_of_study=user_in.field_of_study,
        preferred_degree=user_in.preferred_degree,
        current_degree=user_in.current_degree,
        home_university=user_in.home_university,
        graduation_year=user_in.graduation_year,
        english_test=user_in.english_test,
        english_score=user_in.english_score,
        toefl_score=user_in.toefl_score,
        gre_score=user_in.gre_score,
        gmat_score=user_in.gmat_score,
        work_experience_years=user_in.work_experience_years,
        intake_preference=user_in.intake_preference,
        ranking_preference=user_in.ranking_preference,
        scholarship_interest=user_in.scholarship_interest,
        work_abroad_interest=user_in.work_abroad_interest,
    )

    if existing:
        # Resend OTP — update existing unverified user
        existing.hashed_password = get_password_hash(user_in.password)
        for k, v in profile_fields.items():
            setattr(existing, k, v)
        existing.otp = otp
        existing.otp_expires_at = expires
        db.commit()
        user = existing
    else:
        user = User(
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            is_verified=False,
            otp=otp,
            otp_expires_at=expires,
            **profile_fields,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    background_tasks.add_task(send_otp_email, user.email, otp)
    response: dict = {"email": user.email, "message": "OTP sent to your email. Please verify to activate your account."}
    # Dev mode: return OTP in response when no email service is configured
    if not os.getenv("EMAIL_USER"):
        response["dev_otp"] = otp
        response["dev_note"] = "No email configured — OTP returned here for development. Remove in production."
    return response


@router.post("/send-otp", response_model=dict)
def send_otp(req: OTPRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> Any:
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this email.")
    
    otp = generate_otp()
    user.otp = otp
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
    db.commit()
    
    background_tasks.add_task(send_otp_email, user.email, otp)
    response: dict = {"message": "OTP sent to your email."}
    if not os.getenv("EMAIL_USER"):
        response["dev_otp"] = otp
    return response


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
