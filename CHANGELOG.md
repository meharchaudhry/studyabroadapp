# StudyPathway — Changelog

## Latest Updates (April 2026)

### AI Coach — Major Overhaul
- **Gemini 2.5 Flash** is now the primary AI (replaced deprecated `google.generativeai` gRPC SDK with `google.genai` REST SDK — fixes DNS/gRPC failures)
- **Timeline Tab** — 3-step questionnaire: intake month/year + country → test status (IELTS/GRE done/planned/not started) → application stage checkboxes. Generates a personalised month-by-month plan with Google Calendar `.ics` export
- **Profile Analysis** — 7-dimension scoring: Academic (30pts) + English (20pts) + GRE/GMAT (10pts) + Experience (15pts) + Financial (10pts) + Completeness (10pts) + Clarity (5pts). Shows bar chart per dimension, grade badge, strengths, gaps, and country fit
- **Document Checklist** — 15-country support with category groupings, key tips, visa fee, and timeline weeks. AI-personalised checklist generated from user profile
- **Germany APS warning** shown inline when Germany is selected

### Visa Guide + RAG Pipeline
- **Hybrid RAG** — 4-leg retrieval: Dense semantic + BM25 keyword + country-filtered dense + HyDE (Hypothetical Document Embedding), merged with Reciprocal Rank Fusion (RRF)
- **`GeminiEmbeddings`** — custom LangChain-compatible embeddings using REST API (`models/gemini-embedding-001`), replaces broken `langchain_google_genai` gRPC embeddings
- **33 visa documents ingested** — 1,136 chunks across UK, USA, Canada, Australia, Germany, France, Netherlands, Ireland, Singapore, Japan, Sweden, Norway, Denmark, Finland, New Zealand, UAE, Portugal, Italy, Spain, South Korea, Switzerland + topic guides
- **Country priority fix** — query-mentioned country now overrides the UI dropdown (asking "Spain visa" while UK is selected correctly returns Spain info)
- **Retry with backoff** — automatic 3× retry on Gemini 503/429 transient errors
- **Adaptive response length** — detailed questions (documents, process, timeline) get 4096 token budget; simple factual questions get 2048
- **Graceful error handling** — transient API failures return friendly message instead of 500/white-screen crash
- **Source rendering fix** — sources shown as filenames (not raw JS objects, which caused React white-screen crash)

### Housing
- `SEARCH_LINKS` constant added to `housing_scraper.py` — fixes `ImportError` on startup for countries with platform guides but no live scraper

### Infrastructure
- Backend must run with `/opt/anaconda3/bin/uvicorn` (conda Python 3.11) not system Python 3.13
- ChromaDB collection `visa_policies` — persistent at `backend/data/chroma_db/`
- All AI keys read from `backend/.env` via pydantic `BaseSettings`
