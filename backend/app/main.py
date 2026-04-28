from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="StudyPathway API",
    description="AI-powered Study Abroad Intelligence Platform for Indian Students",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import auth, visa, university, jobs, decision, housing, appointments, ai, finance, calendar, cv_upload
from app.core.config import settings

app.include_router(auth.router,         prefix=f"{settings.API_V1_STR}/auth",         tags=["auth"])
app.include_router(visa.router,         prefix=f"{settings.API_V1_STR}/visa",         tags=["visa"])
app.include_router(university.router,   prefix=f"{settings.API_V1_STR}/universities", tags=["universities"])
app.include_router(jobs.router,         prefix=f"{settings.API_V1_STR}/jobs",         tags=["jobs"])
app.include_router(decision.router,     prefix=f"{settings.API_V1_STR}/decision",     tags=["decision"])
app.include_router(housing.router,      prefix=f"{settings.API_V1_STR}/housing",      tags=["housing"])
app.include_router(appointments.router, prefix=f"{settings.API_V1_STR}/appointments", tags=["appointments"])
app.include_router(ai.router,           prefix=f"{settings.API_V1_STR}/ai",           tags=["ai"])
app.include_router(finance.router,      prefix=f"{settings.API_V1_STR}/finance",      tags=["finance"])
app.include_router(calendar.router,     prefix=f"{settings.API_V1_STR}/calendar",     tags=["calendar"])
app.include_router(cv_upload.router,    prefix=f"{settings.API_V1_STR}/cv",            tags=["cv"])

@app.get("/")
def read_root():
    return {"message": "Welcome to StudyPathway API v2.0", "docs": "/docs"}
