# Udaan — AI-Powered Study Abroad Platform for Indian Students

Udaan (Hindi: *flight*) is a full-stack, AI-driven platform that consolidates the entire study abroad journey for Indian students — from university discovery to visa guidance, document preparation, financial planning, and job market research — into a single personalised platform.

## Features

- 🎓 **2,942 Universities** — Browse across 20+ countries with real QS/THE rankings, tuition in INR, CGPA/IELTS/GRE requirements, and personalised match scores
- 🤖 **AI Recommendation Engine** — 13-factor hybrid scoring (rule-based + Gemini LLM) producing explainable, personalised university matches
- 🛂 **Visa RAG Chatbot** — Four-stage retrieval pipeline (hybrid dense+BM25+HyDE → Gemini reranking → LLM generation) over 104 visa documents across 20+ countries
- 🧠 **5-Agent Decision Chain** — Sequential agents for profile fit, visa difficulty, financial ROI, and job market quality, synthesised by Gemini into a top-3 ranked shortlist
- 📋 **AI Study Tools** — SOP Builder, Application Timeline, Document Checklist, and Profile Gap Analyser, all powered by Gemini
- 📄 **CV Extraction** — Upload a PDF/DOCX CV; Gemini Vision extracts your academic profile and autofills the form
- 💰 **Finance ROI Calculator** — Break-even years, 5-year net return, and monthly loan repayment by country and career goal
- 💼 **Jobs Portal** — Post-study work portal with country-by-country job market scores and portal listings
- 🏘️ **Housing Finder** — Student accommodation data by country with cost estimates
- 📅 **Google Calendar Sync** — Push all application deadlines directly to Google Calendar with 7-day reminders
- ✉️ **OTP Email Auth** — Secure registration with 6-digit OTP verification via Gmail SMTP

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite, Tailwind CSS, React Router, Axios, Chart.js |
| Backend | FastAPI (Python), SQLAlchemy ORM, Alembic migrations |
| AI / ML | Google Gemini 2.5 Flash, Gemini Embedding 001, ChromaDB, BM25 (rank_bm25) |
| Database | PostgreSQL (Supabase) |
| Auth | JWT (30-day) + OTP email verification (bcrypt, Gmail SMTP) |
| Automation | n8n workflows (visa ingest, jobs refresh, housing refresh) |

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/          # 11 FastAPI routers (auth, visa, universities, ai, decision, ...)
│   │   ├── services/     # rag.py, recommendation.py, decision_chain.py, ai_agent.py, ...
│   │   ├── models/       # SQLAlchemy models
│   │   └── core/         # config, database, security
│   ├── data/
│   │   ├── visa_docs/    # 104 Markdown documents (RAG knowledge base)
│   │   ├── eval_charts/  # RAG evaluation visualisations
│   │   └── ...           # universities.csv, housing, jobs, visa JSON data
│   ├── scripts/          # ingest_visa.py, evaluate_rag.py, seed_db.py, scrape_*.py
│   └── n8n/workflows/    # 21_visa, 22_jobs, 23_housing payload ingest workflows
└── frontend/
    └── src/
        ├── pages/        # 15 pages: Login, Register, Dashboard, Universities, VisaChat, ...
        ├── api/          # Axios API clients per feature
        └── components/   # AuthGuard, Layout
```

## Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL (or Supabase project)
- Google Gemini API key
- Gmail account (for OTP SMTP)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:

```env
DATABASE_URL=postgresql://user:password@host/dbname
DIRECT_DATABASE_URL=postgresql://user:password@host/dbname
SECRET_KEY=your_jwt_secret_key
ALGORITHM=HS256
GOOGLE_API_KEY=your_gemini_api_key
EMAIL_USER=your_gmail@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
ADZUNA_APP_ID=your_adzuna_id
ADZUNA_APP_KEY=your_adzuna_key
```

Run database migrations:

```bash
alembic upgrade head
```

Seed the university database:

```bash
python scripts/seed_universities.py
```

Build the ChromaDB vector store (RAG knowledge base):

```bash
python scripts/ingest_visa.py
```

Start the backend:

```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`. The frontend proxies API calls to `http://127.0.0.1:8000/api/v1`.

### University Ranking Data (optional rebuild)

The repository includes `backend/data/universities.csv` — you can seed directly from this. To rebuild from raw Kaggle QS/THE data:

```bash
pip install kaggle
# configure ~/.kaggle/kaggle.json
python scripts/fetch_kaggle_rankings.py
python scripts/build_university_dataset.py
python scripts/seed_universities.py
```

## API Documentation

Once the backend is running, interactive docs are available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## RAG Evaluation

To run the full evaluation suite (24 queries, 8 metrics):

```bash
cd backend
source venv/bin/activate
python scripts/evaluate_rag.py
python scripts/generate_eval_report.py   # generates charts in data/eval_charts/
```

| Metric | Score |
|---|---|
| Hit Rate @ 6 | 0.950 |
| MRR @ 6 | 0.950 |
| MAP @ 6 | 0.839 |
| NDCG @ 6 | 0.899 |
| Faithfulness | 0.825 |
| Answer Relevancy | 0.779 |
| Keyword Coverage | 0.870 |
| Guardrail Accuracy | 1.000 |
| **Overall** | **0.866** |

## n8n Automation Workflows

Three n8n workflows are included in `backend/n8n/workflows/`:

| Workflow | Description |
|---|---|
| `21_visa_payload_direct_ingest.json` | Trigger visa document reingest via webhook |
| `22_jobs_payload_direct_ingest.json` | Trigger jobs data refresh via webhook |
| `23_housing_payload_direct_ingest.json` | Trigger housing data refresh via webhook |

See `backend/n8n/N8N_CLOUD_LOCAL_BACKEND_SETUP.md` for setup instructions.

## Environment Notes

- ChromaDB (`backend/data/chroma_db/`) is excluded from git — run `ingest_visa.py` after cloning to rebuild it (~5 minutes, requires Gemini API key)
- `backend/data/google_credentials.json` (Google Calendar OAuth) is excluded from git — generate your own from Google Cloud Console
- The backend CORS config allows `localhost:5173` and `localhost:5174` (Vite's default and fallback ports)
