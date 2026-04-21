from pydantic import BaseModel, EmailStr
from typing import List, Optional

# ── Academic Schemas ─────────────────────────────────────────────────────────

class DegreeBase(BaseModel):
    degree_level: str
    specialization: str
    cgpa: float
    institution: Optional[str] = None
    year_graduated: Optional[str] = None

class DegreeCreate(DegreeBase):
    pass

class DegreeResponse(DegreeBase):
    id: int
    class Config:
        from_attributes = True

class TestScoreBase(BaseModel):
    test_name: str
    score: float
    test_date: Optional[str] = None

class TestScoreCreate(TestScoreBase):
    pass

class TestScoreResponse(TestScoreBase):
    id: int
    class Config:
        from_attributes = True

# ── User Schemas ─────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    current_degree: Optional[str] = None
    home_university: Optional[str] = None
    field_of_study: Optional[str] = None
    cgpa: Optional[float] = None
    graduation_year: Optional[int] = None
    english_test: Optional[str] = None
    english_score: Optional[float] = None
    toefl_score: Optional[int] = None
    gre_score: Optional[int] = None
    gmat_score: Optional[int] = None
    work_experience_years: Optional[float] = None
    preferred_degree: Optional[str] = None
    intake_preference: Optional[str] = None
    ranking_preference: Optional[str] = None
    work_abroad_interest: Optional[bool] = None
    budget_inr: Optional[int] = None
    scholarship_interest: Optional[bool] = None
    budget: Optional[int] = None
    target_countries: Optional[List[str]] = None
    
    # Nested Collections
    degrees: Optional[List[DegreeCreate]] = []
    tests: Optional[List[TestScoreCreate]] = []

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_verified: bool
    budget: Optional[int]
    target_countries: Optional[List[str]]
    work_experience_years: Optional[int]
    preferred_intake: Optional[str]
    career_goal: Optional[str]
    preferred_environment: Optional[str]
    study_priority: Optional[str]
    learning_style: Optional[str]
    living_preference: Optional[str]
    
    # Nested Collections
    degrees: List[DegreeResponse] = []
    tests: List[TestScoreResponse] = []

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
