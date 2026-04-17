# 🌏 StudyPathway — AI-Powered Study Abroad Platform for Indian Students

A full-stack, AI-driven platform designed to help Indian students navigate international higher education — from finding the right university to booking visa consultations.

## Features

- 🎓 **500+ Universities** – Browse across USA, UK, Germany, Australia, Singapore and more with real QS rankings, tuition in INR, and exact Indian admission requirements (CGPA, IELTS, TOEFL, GRE)
- 🤖 **AI Recommendation Engine** – Get personalized university matches based on your academic profile (CGPA, budget, target countries)
- 🏠 **Live Housing Finder** – 600+ student accommodations with INR prices, distance from campus, amenities and student-friendly filters
- 📋 **Visa AI Chatbot** – AI-powered Visa Guidance Bot using RAG over country-specific visa docs (US, UK, Canada, Australia, Germany, etc.)
- 💼 **Job Portal** – Browse study-friendly jobs by country and search live listings via the Adzuna API
- 📅 **Consultant Booking** – Book advisory appointments and download `.ics` calendar events directly to Google Calendar
- ✉️ **OTP Email Auth** – Secure OTP-based verification flow using Gmail SMTP

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy, PostgreSQL |
| AI / ML | Google Gemini, ChromaDB, HuggingFace Embeddings (LangChain) |
| Frontend | React + Vite, Tailwind CSS |
| Auth | JWT + OTP Email Verification |
| Database | PostgreSQL + psycopg2 |

## Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Fill in your credentials
uvicorn app.main:app --reload --port 8000
```

### Seed Data
```bash
cd backend
source venv/bin/activate
python scripts/seed_universities.py
python scripts/generate_housing.py
python scripts/scrape_visa.py && python scripts/ingest_visa.py
```

### University Ranking Sources (Kaggle)
1. Add your QS and THE Kaggle dataset links in `backend/data/university_sources.json`.
2. Make sure Kaggle CLI is configured locally:
```bash
pip install kaggle
mkdir -p ~/.kaggle
# put kaggle.json from your Kaggle account in ~/.kaggle/kaggle.json
chmod 600 ~/.kaggle/kaggle.json
```
3. Download raw ranking files:
```bash
cd backend
source venv/bin/activate
python scripts/fetch_kaggle_rankings.py
```

Downloaded files will be stored under `backend/data/raw_rankings/`.

4. Build merged university dataset (QS + THE):
```bash
python scripts/build_university_dataset.py
```

5. Seed merged data into DB:
```bash
python scripts/seed_universities.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Create a `backend/.env` file:

```env
DATABASE_URL=postgresql://user:password@localhost/studypathway
SECRET_KEY=your_jwt_secret_key
EMAIL_USER=your_gmail@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
GEMINI_API_KEY=your_gemini_key
ADZUNA_APP_ID=your_adzuna_id
ADZUNA_APP_KEY=your_adzuna_key
```
