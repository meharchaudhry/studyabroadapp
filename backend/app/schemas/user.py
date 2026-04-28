from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional


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
    target_countries: Optional[List[str]] = None
    intake_preference: Optional[str] = None
    ranking_preference: Optional[str] = None
    scholarship_interest: Optional[bool] = None
    work_abroad_interest: Optional[bool] = None
    career_goal: Optional[str] = None
    preferred_environment: Optional[str] = None
    study_priority: Optional[str] = None
    learning_style: Optional[str] = None
    living_preference: Optional[str] = None
    
    # Nested Collections
    degrees: Optional[List[DegreeCreate]] = Field(default_factory=list)
    tests: Optional[List[TestScoreCreate]] = Field(default_factory=list)


class UserUpdate(BaseModel):
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
    preferred_intake: Optional[str] = None
    ranking_preference: Optional[str] = None
    work_abroad_interest: Optional[bool] = None
    budget_inr: Optional[int] = None
    budget: Optional[int] = None
    scholarship_interest: Optional[bool] = None
    target_countries: Optional[List[str]] = None
    career_goal: Optional[str] = None
    preferred_environment: Optional[str] = None
    study_priority: Optional[str] = None
    learning_style: Optional[str] = None
    living_preference: Optional[str] = None
    current_password: Optional[str] = None
    password: Optional[str] = None
    degrees: Optional[List[DegreeCreate]] = Field(default_factory=list)
    tests: Optional[List[TestScoreCreate]] = Field(default_factory=list)

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_verified: bool
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

    cgpa: Optional[float] = None
    field_of_study: Optional[str] = None
    preferred_degree: Optional[str] = None
    current_degree: Optional[str] = None
    home_university: Optional[str] = None
    graduation_year: Optional[int] = None

    english_score: Optional[float] = None
    english_test: Optional[str] = None
    toefl_score: Optional[int] = None
    gre_score: Optional[int] = None
    gmat_score: Optional[int] = None
    work_experience_years: Optional[float] = None

    budget: Optional[int] = None
    budget_inr: Optional[int] = None
    target_countries: Optional[List[str]] = None
    intake_preference: Optional[str] = None
    ranking_preference: Optional[str] = None
    scholarship_interest: Optional[bool] = None
    work_abroad_interest: Optional[bool] = None

    # Legacy keys kept optional for backward compatibility with older clients.
    preferred_intake: Optional[str] = None
    career_goal: Optional[str] = None
    preferred_environment: Optional[str] = None
    study_priority: Optional[str] = None
    learning_style: Optional[str] = None
    living_preference: Optional[str] = None
    
    # Resume
    resume_filename: Optional[str] = None   # filename of uploaded CV (never send full text)

    # Nested Collections
    degrees: List[DegreeResponse] = Field(default_factory=list)
    tests: List[TestScoreResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
