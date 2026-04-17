# n8n Workflow Pack (Data Collection)

There are two workflow styles in this folder:

1. `11/12/13` = monitor sources and trigger backend refresh scripts.
2. `21/22/23` = pull data in n8n and push parsed payloads directly to backend ingest endpoints.

For your current setup, use direct-ingest:

- 21_visa_payload_direct_ingest.json
- 22_jobs_payload_direct_ingest.json
- 23_housing_payload_direct_ingest.json

## What each direct-ingest workflow now does

### 21_visa_payload_direct_ingest.json
1. `Weekly Trigger` runs on schedule.
2. `Get Dataset Countries` reads `/api/v1/universities/countries` from your backend.
3. `Build Official Visa Sources` maps countries to official visa pages (Gov UK, Canada IRCC, US Travel State, Australia Home Affairs).
4. `Fetch Official Visa Pages` downloads those pages.
5. `Build Visa Ingest Payload` extracts text and builds `countries` + `documents` payload.
6. `POST Visa Ingest Payload` sends data to `/api/v1/automation/ingest/visa`.

### 22_jobs_payload_direct_ingest.json
1. `Sunday Trigger` runs on schedule.
2. `Fetch Remotive Jobs` calls the free Remotive API: `https://remotive.com/api/remote-jobs`.
3. `Build Jobs Ingest Payload` filters for student/entry roles (graduate/intern/junior/entry/student/trainee) and normalizes fields.
4. `POST Jobs Ingest Payload` sends to `/api/v1/automation/ingest/jobs`.

### 23_housing_payload_direct_ingest.json
1. `Sunday Trigger` runs on schedule.
2. `Get Dataset Countries` reads `/api/v1/universities/countries`.
3. `Build Housing Sources` creates Numbeo country cost URLs (free public pages).
4. `Fetch Housing Cost Pages` downloads those pages.
5. `Build Housing Ingest Payload` extracts a rent benchmark and creates student-friendly listing payloads.
6. `POST Housing Ingest Payload` sends to `/api/v1/automation/ingest/housing`.

## Required n8n variables

Set these in n8n Variables:

- `BACKEND_BASE_URL` = your backend base URL reachable from n8n
- `N8N_AUTOMATION_TOKEN` = same value as backend `N8N_WEBHOOK_TOKEN`

## What is BACKEND_BASE_URL and how to get it

Use one of these free options:

1. Backend already deployed (Render/Railway/Fly/Heroku-like):
   - Use that URL directly, for example `https://your-app.onrender.com`.

2. Backend running locally on your laptop (`http://localhost:8000`):
   - n8n on same machine: use `http://host.docker.internal:8000` (if n8n in Docker) or `http://localhost:8000` (if n8n desktop/local process).
   - n8n hosted in cloud: expose local backend with a free tunnel and use that URL.

3. Free tunnel options (no paid requirement):
   - `cloudflared tunnel --url http://localhost:8000`
   - `npx localtunnel --port 8000`
   - Use the generated `https://...` URL as `BACKEND_BASE_URL`.

Quick check after setting variable:
- Open `{{BACKEND_BASE_URL}}/api/v1/universities/countries` in browser; you should get JSON.

## Required backend env

Set in backend `.env`:

- `N8N_WEBHOOK_TOKEN=<your_shared_secret>`

Then restart backend.

## Why you previously saw only 3 simple steps

Those previous files were starter templates with example payload objects, not finished ETL pipelines.
The updated `21/22/23` files now include actual fetch + transform + ingest steps.

## Manual edits you may want in n8n UI

1. Adjust schedule times/cron expressions.
2. Add Slack/Email notification nodes on failure branches.
3. Add retry policy in each HTTP node (2-3 retries).
4. Tune country/source mapping inside `Build Official Visa Sources` for any extra countries.

## Important note

11/12/13 use source monitoring + backend-trigger pattern.

21/22/23 use direct-ingest pattern and are the preferred option when n8n already has parsed payloads ready.
