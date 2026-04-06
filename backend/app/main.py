from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="StudyPathway API",
    description="AI-powered Study Abroad Intelligence Platform for Indian Students",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import auth, visa, university, jobs, decision, housing
from app.core.config import settings

app.include_router(auth.router,       prefix=f"{settings.API_V1_STR}/auth",         tags=["auth"])
app.include_router(visa.router,       prefix=f"{settings.API_V1_STR}/visa",         tags=["visa"])
app.include_router(university.router, prefix=f"{settings.API_V1_STR}/universities", tags=["universities"])
app.include_router(jobs.router,       prefix=f"{settings.API_V1_STR}/jobs",         tags=["jobs"])
app.include_router(decision.router,   prefix=f"{settings.API_V1_STR}/decision",     tags=["decision"])
app.include_router(housing.router,    prefix=f"{settings.API_V1_STR}/housing",      tags=["housing"])

@app.get("/")
def read_root():
    return {"message": "Welcome to StudyPathway API v2.0", "docs": "/docs"}
