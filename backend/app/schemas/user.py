from pydantic import BaseModel, EmailStr
from typing import List, Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

    # Academic background
    cgpa: Optional[float] = None
    field_of_study: Optional[str] = None
    preferred_degree: Optional[str] = None
    current_degree: Optional[str] = None
    home_university: Optional[str] = None
    graduation_year: Optional[int] = None

    # Test scores
    english_test: Optional[str] = None    # "IELTS" | "TOEFL" | "PTE" | "Duolingo"
    english_score: Optional[float] = None  # IELTS band or PTE score
    toefl_score: Optional[int] = None
    gre_score: Optional[int] = None
    gmat_score: Optional[int] = None
    work_experience_years: Optional[float] = None

    # Goals & budget
    budget: Optional[int] = None            # USD/year (derived server-side from budget_inr)
    budget_inr: Optional[int] = None        # INR/year (user input)
    target_countries: Optional[List[str]] = []
    intake_preference: Optional[str] = None
    ranking_preference: Optional[str] = None
    scholarship_interest: Optional[bool] = None
    work_abroad_interest: Optional[bool] = None
    # Career & lifestyle preferences
    career_goal: Optional[str] = None
    study_priority: Optional[str] = None
    preferred_environment: Optional[str] = None
    learning_style: Optional[str] = None
    living_preference: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_verified: bool
    full_name: Optional[str] = None

    # Academic
    cgpa: Optional[float] = None
    field_of_study: Optional[str] = None
    preferred_degree: Optional[str] = None
    current_degree: Optional[str] = None
    home_university: Optional[str] = None
    graduation_year: Optional[int] = None

    # Test scores
    english_test: Optional[str] = None
    english_score: Optional[float] = None
    toefl_score: Optional[int] = None
    gre_score: Optional[int] = None
    gmat_score: Optional[int] = None
    work_experience_years: Optional[float] = None

    # Goals & budget
    budget: Optional[int] = None
    budget_inr: Optional[int] = None
    target_countries: Optional[List[str]] = None
    intake_preference: Optional[str] = None
    ranking_preference: Optional[str] = None
    scholarship_interest: Optional[bool] = None
    work_abroad_interest: Optional[bool] = None
    # Career & lifestyle preferences
    career_goal: Optional[str] = None
    study_priority: Optional[str] = None
    preferred_environment: Optional[str] = None
    learning_style: Optional[str] = None
    living_preference: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
