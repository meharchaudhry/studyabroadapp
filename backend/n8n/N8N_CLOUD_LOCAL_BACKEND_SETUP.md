# n8n Cloud -> Local Backend Setup (Exact Steps)

This guide is for your current setup:
- n8n is on n8n Cloud
- backend runs locally on your laptop
- n8n must call your local backend securely

## 1. Set backend token in .env

Open backend/.env and confirm this exists:

```env
N8N_WEBHOOK_TOKEN=your_long_random_secret
```

If you need a new secret, generate one:

```bash
openssl rand -hex 32
```

Then restart backend after any .env change.

## 2. Start backend locally

From backend folder, run your API server (example):

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Quick local check:

```bash
curl http://localhost:8000/api/v1/universities/countries
```

You should get JSON.

## 3. Create n8n credential (when Variables are not available)

In n8n Cloud UI:

1. Go to Credentials.
2. Click New Credential.
3. Search for Header Auth (or HTTP Header Auth).
4. Create a credential with:
   - Name: Automation Token
   - Header Name: X-Automation-Token
   - Header Value: same value as N8N_WEBHOOK_TOKEN in backend/.env
5. Save.

If your workspace does not show Header Auth credential type:
- Use the HTTP Request node directly.
- Turn on Send Headers.
- Add header manually:
  - Name: X-Automation-Token
  - Value: your token

## 4. Create a public tunnel for local backend (free)

Recommended: Cloudflare Tunnel.

Install once on macOS:

```bash
brew install cloudflared
```

Start tunnel:

```bash
cloudflared tunnel --url http://localhost:8000
```

It will print a public URL like:

```text
https://random-subdomain.trycloudflare.com
```

Keep this tunnel terminal open while testing/running workflows.

Alternative free option:

```bash
npx localtunnel --port 8000
```

## 5. Wire n8n workflow HTTP nodes to your tunnel URL

In each workflow HTTP Request node, set full URL (no variable required):

- Visa ingest:
  - https://YOUR_TUNNEL_URL/api/v1/automation/ingest/visa
- Jobs ingest:
  - https://YOUR_TUNNEL_URL/api/v1/automation/ingest/jobs
- Housing ingest:
  - https://YOUR_TUNNEL_URL/api/v1/automation/ingest/housing

Also set auth in each HTTP Request node:

- Authentication: select your Automation Token credential
- Or if manual headers: include X-Automation-Token header

For nodes that fetch countries, set URL to:

- https://YOUR_TUNNEL_URL/api/v1/universities/countries

## 6. Validate tunnel reachability before running n8n

From browser or terminal, test:

```bash
curl https://YOUR_TUNNEL_URL/api/v1/universities/countries
```

If this fails, n8n Cloud cannot reach your backend yet.

## 7. Run workflow test in n8n

1. Open workflow 21, click Execute Workflow.
2. Confirm final HTTP node response is 200.
3. Repeat for workflow 22 and workflow 23.

Expected backend effects:
- /ingest/visa writes data/visa_data.json and data/visa_docs/*.md then rebuilds embeddings.
- /ingest/jobs writes data/local_jobs.csv then seeds jobs DB.
- /ingest/housing writes data/live_housing.json.

## 8. Common errors and fixes

- 401 Unauthorized:
  - Token mismatch. Ensure n8n header value exactly equals N8N_WEBHOOK_TOKEN.

- 404 Not Found:
  - Wrong URL path. Recheck /api/v1/automation/ingest/... endpoints.

- Timeout / Could not connect:
  - Tunnel not running, wrong tunnel URL, or backend not running on 8000.

- 503 N8N_WEBHOOK_TOKEN not configured:
  - Backend .env missing N8N_WEBHOOK_TOKEN or backend not restarted.

## 9. Daily usage checklist

1. Start backend.
2. Start tunnel.
3. Confirm countries endpoint via tunnel URL.
4. Run/schedule n8n workflows.

If tunnel URL changes, update URLs in n8n HTTP Request nodes.
