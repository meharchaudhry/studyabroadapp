# StudyPathway Implementation Status

This document is a strict audit of what is actually working end-to-end in the current codebase, and what is still missing before the app can be called fully functional.

I only counted something as "implemented" if the code path exists and is backed by a real backend/data flow, not just a placeholder, mock array, static UI, or hardcoded demo state.

## What Is Implemented Today

- Authentication with OTP is implemented in the backend, including register, send OTP, verify OTP, login, get profile, and update profile flows in [backend/app/api/auth.py](backend/app/api/auth.py).
- OTP emails are sent through the SMTP notification service in [backend/app/services/notification.py](backend/app/services/notification.py), with a fallback print-only path if SMTP credentials are missing.
- The frontend auth flow is wired end-to-end through [frontend/src/api/auth.js](frontend/src/api/auth.js), [frontend/src/pages/Login.jsx](frontend/src/pages/Login.jsx), [frontend/src/pages/Register.jsx](frontend/src/pages/Register.jsx), and [frontend/src/pages/OTPVerify.jsx](frontend/src/pages/OTPVerify.jsx).
- University browsing is implemented through live backend endpoints for country filter, list, detail, and recommendations in [backend/app/api/university.py](backend/app/api/university.py).
- University browsing and recommendation UI is connected in [frontend/src/pages/Universities.jsx](frontend/src/pages/Universities.jsx), and it calls the real API instead of using fixed demo cards.
- The decision dashboard is implemented as a real backend-driven flow in [backend/app/api/decision.py](backend/app/api/decision.py) and [backend/app/services/decision_chain.py](backend/app/services/decision_chain.py), with the frontend consuming it in [frontend/src/pages/Dashboard.jsx](frontend/src/pages/Dashboard.jsx).
- The decision chain is not just one model call; it actually combines profile fit, visa, finance, and jobs signals before returning ranked recommendations in [backend/app/services/decision_chain.py](backend/app/services/decision_chain.py).
- Visa checklist lookup is implemented through [backend/app/api/visa.py](backend/app/api/visa.py), which reads the local visa dataset and returns country-specific requirements.
- Visa Q&A is implemented through a working RAG baseline in [backend/app/services/rag.py](backend/app/services/rag.py) and is surfaced in [frontend/src/pages/VisaChat.jsx](frontend/src/pages/VisaChat.jsx).
- Jobs browsing is implemented through live portal metadata and live search in [backend/app/api/jobs.py](backend/app/api/jobs.py), and the frontend is wired in [frontend/src/pages/Jobs.jsx](frontend/src/pages/Jobs.jsx).
- Jobs can be saved to the user profile through the backend save endpoint in [backend/app/api/jobs.py](backend/app/api/jobs.py).
- Housing listings are implemented through [backend/app/api/housing.py](backend/app/api/housing.py), with filtering by country, price, and student-friendliness.
- Housing browsing is wired in [frontend/src/pages/Housing.jsx](frontend/src/pages/Housing.jsx) and uses the backend data rather than only static cards.
- The backend includes automation endpoints for n8n payload ingestion and refresh workflows in [backend/app/api/automation.py](backend/app/api/automation.py).
- The n8n workflow pack now includes direct ingest flows and setup documentation in [backend/n8n/workflows/README.md](backend/n8n/workflows/README.md) and [backend/n8n/N8N_CLOUD_LOCAL_BACKEND_SETUP.md](backend/n8n/N8N_CLOUD_LOCAL_BACKEND_SETUP.md).
- The backend app is wired with the real routers for auth, visa, universities, jobs, decision, housing, and automation in [backend/app/main.py](backend/app/main.py).

## What Is Partially Working But Not Counted As Fully Implemented

- The Finance page works as a frontend calculator in [frontend/src/pages/Finance.jsx](frontend/src/pages/Finance.jsx), but it is still a client-side calculator rather than a dedicated backend finance service.
- The RAG evaluation dashboard exists in [frontend/src/pages/RAGEvaluation.jsx](frontend/src/pages/RAGEvaluation.jsx), but the numbers are hardcoded and therefore do not count as a real evaluation system.
- The visa RAG backend returns basic metrics from [backend/app/services/rag.py](backend/app/services/rag.py), but those metrics are placeholder-style scores, not a full evaluation framework.
- The housing data is functional through the API, but the current dataset is still local file based rather than a fully verified live marketplace integration.
- The jobs experience is usable, but live results still depend on external API credentials and source availability, so it is not a fully self-contained production pipeline yet.

## What Still Needs To Be Implemented

- A real RAG evaluation backend is missing, including stored evaluation runs, golden test sets, and reproducible reports for faithfulness, answer relevancy, context precision, and context recall.
- Ranking metrics for the RAG system are missing, including MRR, MAP, nDCG, Precision@K, and Recall@K.
- The current RAG response pipeline needs a proper evaluation harness so the metrics are computed from test data instead of being returned as simple placeholder values.
- The LLM behavior is not deterministic yet, because [backend/app/services/rag.py](backend/app/services/rag.py) and [backend/app/services/decision_chain.py](backend/app/services/decision_chain.py) still use `temperature=0.2`.
- If the same question should always return the same answer, the temperature needs to be set to `0.0`, and any remaining variability in prompts or retrieval order needs to be removed.
- A production-ready AI justification layer is missing, meaning the app does not yet clearly explain when AI is used, why it is used, and where deterministic rules are better than model output.
- The OTP flow needs proper production email validation and deliverability testing, because the current SMTP path will fall back to console output if credentials are absent or invalid.
- A deployed backend and frontend are still missing, so the app is not hosted yet and cannot be used as a live public product.
- Production deployment work is still needed, including choosing a host, setting environment variables, running migrations, and making sure the API and frontend are reachable by a public URL.
- The finance feature needs a real backend endpoint if it is supposed to be part of the core platform rather than only a frontend utility.
- The RAG page needs real backend-fed metrics and result history instead of the current static scorecards and mock test rows.
- The app still needs a clearer, final AI policy for the report and UI, so it is obvious which screens use AI, which screens use rules, and why.

## RAG-Specific Gaps

- The current visa assistant uses Chroma plus HuggingFace embeddings and Gemini in [backend/app/services/rag.py](backend/app/services/rag.py), so the baseline answer flow exists.
- The RAG stack does not yet include hybrid retrieval with BM25 plus dense retrieval and reciprocal rank fusion.
- The RAG stack does not yet include a cross-encoder reranker, so retrieval quality is still simpler than a production-grade setup.
- The RAG stack does not yet store evaluation outputs, so there is no historical experiment tracking for prompts, metrics, or retrieval changes.
- The RAG stack does not yet surface grounded evaluation reports to the frontend, so the evaluation page is still a visual mock rather than a real analytics tool.

## Frontend Status

- The main app routing is in place in [frontend/src/App.jsx](frontend/src/App.jsx), including login, register, OTP verification, dashboard, universities, housing, appointments, visa chat, jobs, finance, evaluation, and profile routes.
- The auth guard and layout structure exist and are functional, so protected routes are separated from public routes.
- The dashboard is one of the strongest working frontend pieces because it renders the live decision response and agent steps instead of static content.
- The universities, jobs, housing, and visa chat screens are connected to backend APIs and are not just static pages.
- The finance screen is functional as a local calculator, but it still needs backend integration if it should be treated as a product feature instead of a utility.
- The evaluation screen is not yet a real dashboard, because it still uses static demo data and hardcoded score values.

## Backend Status

- The backend API surface is coherent and already includes auth, universities, visa, jobs, housing, decision, and automation routers in [backend/app/main.py](backend/app/main.py).
- User profile storage supports richer fields such as degrees, tests, budget, target countries, work experience, preferred intake, career goal, learning style, and living preference in [backend/app/api/auth.py](backend/app/api/auth.py).
- University recommendations are profile-aware and explain why a university matched, using [backend/app/services/recommendation.py](backend/app/services/recommendation.py).
- The decision chain combines multiple signals and is not just a single prompt wrapper, which is a real functional improvement over a pure demo chat flow in [backend/app/services/decision_chain.py](backend/app/services/decision_chain.py).
- The visa assistant has a working local data ingestion model, but its evaluation layer still needs to be upgraded before it can be called complete.

## What The App Still Needs Before It Can Be Called Fully Functional

- A deployed backend URL and a deployed frontend URL.
- A stable n8n cloud to backend connection that is tested end-to-end.
- Real RAG evaluation storage and reporting.
- Deterministic model settings.
- A fully documented AI justification layer for the project report and UI.
- A real finance backend if finance is meant to be part of the product.
- Production email verification for OTP.
- A final pass on content, copy, and error handling so the app behaves like a finished product rather than a partially complete course project.

## Bottom Line

- Implemented and working today: auth OTP flow, university browse/recommendations, decision dashboard, visa checklist and baseline RAG chat, jobs browsing/search, housing listings, and automation ingest endpoints.
- Not fully implemented yet: real RAG evaluation metrics, ranking metrics such as MRR and MAP, deterministic LLM output, production deployment, production email verification, and a backend finance service.
- The biggest remaining gap is the RAG stack, because the answer flow exists but the evaluation and quality measurement layer is still incomplete.