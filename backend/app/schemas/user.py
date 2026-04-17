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
