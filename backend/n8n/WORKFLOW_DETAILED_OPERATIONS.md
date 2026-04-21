# n8n Automation: Detailed Operations Guide

This is the practical guide for the three direct-ingest workflows:

- backend/n8n/workflows/21_visa_payload_direct_ingest.json
- backend/n8n/workflows/22_jobs_payload_direct_ingest.json
- backend/n8n/workflows/23_housing_payload_direct_ingest.json

Goal: pull as much relevant free data as possible across multiple countries, transform it, and push into backend ingest endpoints.

## 0. Required setup before running

Backend:

- In backend/.env set:
  - N8N_WEBHOOK_TOKEN=<long_random_secret>
- Restart backend.

n8n:

- If your n8n has Variables, set:
  - BACKEND_BASE_URL
  - N8N_AUTOMATION_TOKEN
- If your n8n does not have Variables, set full URLs + header auth directly in HTTP nodes.

## 1. Workflow 21: Visa payload direct ingest

File: backend/n8n/workflows/21_visa_payload_direct_ingest.json

### What each node does

1. Weekly Trigger
- Runs weekly on cron (currently Monday 07:00).

2. Get Dataset Countries
- Calls /api/v1/universities/countries from your backend.
- This determines the countries to process from your real university dataset.

3. Build Official Visa Sources
- Normalizes country aliases (UK -> United Kingdom, USA -> United States, HongKong -> Hong Kong).
- Uses an internal country -> official_sources map (government/immigration pages).
- Creates one item per country per official source URL.
- Includes metadata for each country:
  - visa_type
  - processing_time
  - visa_fee_inr
  - checklist

4. Fetch Official Visa Pages
- Downloads each official visa page.
- Keeps going even if some pages fail.

5. Build Visa Ingest Payload
- Groups fetched pages by country.
- Strips HTML and keeps summarized text snippets.
- Builds payload:
  - countries object (visa metadata + checklist)
  - documents array (combined source content per country)

6. POST Visa Ingest Payload
- Sends payload to /api/v1/automation/ingest/visa.
- Backend writes visa_data.json + visa_docs/*.md, then rebuilds embeddings.

### What to edit manually

- In Build Official Visa Sources code node:
  - Add countries in sourceMap.
  - Add/replace official_sources links when government pages change.
  - Tune visa_fee_inr and processing_time values.
  - Improve checklist entries by country.

### Where you may need to add links

You should add links for any country present in your universities dataset that is not yet in sourceMap.

Recommended link type:
- Immigration ministry / foreign office / official visa portal.
- Avoid blogs and private consultancy pages.

## 2. Workflow 22: Jobs payload direct ingest

File: backend/n8n/workflows/22_jobs_payload_direct_ingest.json

### What each node does

1. Sunday Trigger
- Runs weekly on Sunday 08:00.

2. Get Dataset Countries
- Pulls countries from your backend dataset to focus results.

3. Fetch Remotive Jobs
- Calls free API: https://remotive.com/api/remote-jobs

4. Fetch Arbeitnow Jobs
- Calls free API: https://www.arbeitnow.com/api/job-board-api

5. Merge Source Fetches
- Waits for both API fetches to complete.

6. Build Jobs Ingest Payload
- Reads both APIs + country list.
- Keeps entry-level signals only:
  - graduate, intern, internship, junior, entry, student, trainee
- Infers country from location text and country aliases.
- Normalizes payload fields for backend ingest.
- Deduplicates jobs by apply link/title/company.
- Caps output to keep runtime stable.

7. POST Jobs Ingest Payload
- Sends to /api/v1/automation/ingest/jobs.
- Backend writes local_jobs.csv and runs seed_jobs.py.

### What to edit manually

- In Build Jobs Ingest Payload code node:
  - Expand entryPattern keywords for your program context.
  - Add more country aliases for location parsing.
  - Tune max rows (currently 800) based on your DB/runtime.

### Where you may need to add links

No manual links required for this workflow right now because it uses free APIs.

If you want more sources, add new HTTP Request nodes for additional free APIs and merge into the code node.

## 3. Workflow 23: Housing payload direct ingest

File: backend/n8n/workflows/23_housing_payload_direct_ingest.json

### What each node does

1. Sunday Trigger
- Runs weekly on Sunday 10:00.

2. Get Dataset Countries
- Reads countries from /api/v1/universities/countries.

3. Build Housing Sources
- Normalizes aliases.
- Uses country -> major cities map.
- Builds Numbeo city URLs for each selected country and city.
- Produces multiple source items per country (not single-country only).

4. Fetch Housing Cost Pages
- Downloads Numbeo city pages.

5. Build Housing Ingest Payload
- Extracts rent benchmarks from city page text.
- Uses fallback country prices if parse is weak.
- Creates multiple listing variants per city:
  - Student Dormitory
  - Private Room in Shared House
  - Studio Apartment
- Generates student-friendly listing objects for ingest.

6. POST Housing Ingest Payload
- Sends payload to /api/v1/automation/ingest/housing.
- Backend writes live_housing.json.

### What to edit manually

- In Build Housing Sources code node:
  - Add/remove countries and cities in cityMap.
- In Build Housing Ingest Payload:
  - Adjust fallback pricing by country.
  - Adjust listing variant multipliers and amenities.

### Where you may need to add links

- Add city-level sources for countries not yet in cityMap.
- You can also add additional free sources by adding new fetch nodes and merging them into payload logic.

## 4. What changed vs your old problem (single country)

- Visa: now processes all supported countries from dataset, and fetches multiple official links per country.
- Jobs: now merges multiple APIs and country-filters from dataset.
- Housing: now uses multiple cities per country, not one country benchmark only.

## 5. Manual checklist after importing workflows in n8n

1. Open each workflow and verify HTTP node URLs:
- /api/v1/universities/countries
- /api/v1/automation/ingest/visa
- /api/v1/automation/ingest/jobs
- /api/v1/automation/ingest/housing

2. Verify header auth:
- X-Automation-Token must match backend N8N_WEBHOOK_TOKEN.

3. Run each workflow manually once.

4. Check backend response in final POST node:
- Should return ok=true.

5. Verify backend files update:
- data/visa_data.json
- data/visa_docs/*.md
- data/local_jobs.csv
- data/live_housing.json

## 6. What you should send me next (to make it even more detailed)

If you want maximum coverage, send me this list and I will wire it in:

- Countries you must support for your course demo.
- Any official visa links your faculty expects to see.
- Any preferred housing/job portals your rubric mentions.

I can then harden the source maps for those countries and deliver a final rubric-aligned automation pack.
