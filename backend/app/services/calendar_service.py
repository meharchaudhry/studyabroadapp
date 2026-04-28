"""
Google Calendar Service — Web OAuth Flow
=========================================
Uses Google OAuth2 web flow (redirect_uri to backend callback).
Token is stored server-side in backend/data/google_token.json.

Setup:
  1. Google Cloud Console → APIs & Services → Enable "Google Calendar API"
  2. Credentials → Create → OAuth 2.0 Client ID → Web application
     - Add Authorised redirect URI:  http://localhost:8000/api/v1/calendar/callback
  3. Download JSON → save as  backend/data/google_credentials.json
  4. User clicks "Connect Google Calendar" in the app → approves → done.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
_BASE             = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CREDENTIALS_FILE  = os.path.join(_BASE, "data", "google_credentials.json")
TOKEN_FILE        = os.path.join(_BASE, "data", "google_token.json")

SCOPES            = ["https://www.googleapis.com/auth/calendar"]
REDIRECT_URI      = "http://localhost:8000/api/v1/calendar/callback"


# ── Helpers ────────────────────────────────────────────────────────────────────

def credentials_exist() -> bool:
    return os.path.exists(CREDENTIALS_FILE)


def token_exists() -> bool:
    return os.path.exists(TOKEN_FILE)


def _load_token():
    """Load saved token from disk. Returns Credentials or None."""
    if not token_exists():
        return None
    try:
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        return creds
    except Exception as e:
        logger.warning("Could not load token: %s", e)
        return None


def _refresh_and_save(creds):
    """Refresh expired token and save back to disk."""
    from google.auth.transport.requests import Request
    creds.refresh(Request())
    _save_token(creds)
    return creds


def _save_token(creds):
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, "w") as fh:
        fh.write(creds.to_json())


def _get_calendar_service():
    """
    Returns authenticated Google Calendar API service.
    Raises FileNotFoundError if credentials.json is missing.
    Raises RuntimeError if not yet authorized (no token).
    """
    from googleapiclient.discovery import build

    if not credentials_exist():
        raise FileNotFoundError(
            "google_credentials.json not found in backend/data/. "
            "Download Web OAuth credentials from Google Cloud Console."
        )

    creds = _load_token()

    if not creds:
        raise RuntimeError("Google Calendar not connected. Please authorize via the app first.")

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds = _refresh_and_save(creds)
        else:
            raise RuntimeError("Google Calendar token expired. Please re-authorize.")

    return build("calendar", "v3", credentials=creds)


# ── OAuth Flow ─────────────────────────────────────────────────────────────────

def get_auth_url() -> str:
    """
    Generate the Google OAuth2 authorization URL.
    User visits this URL, signs in, approves access.
    Google redirects to REDIRECT_URI with ?code=...
    """
    if not credentials_exist():
        raise FileNotFoundError(
            "google_credentials.json not found. "
            "Download Web OAuth2 credentials from Google Cloud Console "
            "and save to backend/data/google_credentials.json"
        )

    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",     # get refresh_token so it doesn't expire
        include_granted_scopes="true",
        prompt="consent",          # force consent screen so refresh_token is always issued
    )
    return auth_url


def exchange_code_for_token(code: str) -> dict:
    """
    Exchange the OAuth2 code (from Google callback) for a token.
    Saves token to disk. Returns {"success": True} or {"success": False, "error": "..."}.
    """
    try:
        from google_auth_oauthlib.flow import Flow
        flow = Flow.from_client_secrets_file(
            CREDENTIALS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI,
        )
        flow.fetch_token(code=code)
        _save_token(flow.credentials)
        logger.info("Google Calendar token saved successfully.")
        return {"success": True}
    except Exception as e:
        logger.error("Token exchange failed: %s", e)
        return {"success": False, "error": str(e)}


def revoke_token() -> dict:
    """Revoke and delete the stored token."""
    try:
        creds = _load_token()
        if creds:
            import requests as _req
            _req.post(
                "https://oauth2.googleapis.com/revoke",
                params={"token": creds.token},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if token_exists():
            os.remove(TOKEN_FILE)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Status ─────────────────────────────────────────────────────────────────────

def check_calendar_auth() -> dict:
    """
    Returns current auth state:
      - not_configured:  credentials.json missing
      - not_connected:   token missing → user needs to authorize
      - connected:       token valid, calendar accessible
      - error:           token exists but API call failed
    """
    if not credentials_exist():
        return {
            "status": "not_configured",
            "authorized": False,
            "message": "Download Web OAuth2 credentials from Google Cloud Console and save to backend/data/google_credentials.json",
        }

    creds = _load_token()
    if not creds:
        return {
            "status": "not_connected",
            "authorized": False,
            "message": "Click 'Connect Google Calendar' to authorize.",
            "auth_url": get_auth_url(),
        }

    try:
        service = _get_calendar_service()
        cal = service.calendarList().get(calendarId="primary").execute()
        return {
            "status": "connected",
            "authorized": True,
            "calendar_name": cal.get("summary", "Primary Calendar"),
            "email": cal.get("id", ""),
        }
    except Exception as e:
        return {
            "status": "error",
            "authorized": False,
            "message": str(e),
            "auth_url": get_auth_url() if credentials_exist() else None,
        }


# ── Event Creation ─────────────────────────────────────────────────────────────

def create_calendar_event(
    title: str,
    start_datetime: datetime,
    description: str = "",
    duration_minutes: int = 60,
    location: str = "",
    timezone: str = "Asia/Kolkata",
) -> dict:
    """
    Creates a real Google Calendar event.
    Returns {"success": True, "event_link": "...", ...} or {"success": False, ...}.
    """
    try:
        service = _get_calendar_service()
        end_dt  = start_datetime + timedelta(minutes=duration_minutes)

        body = {
            "summary":     title,
            "description": description,
            "location":    location,
            "start":  {"dateTime": start_datetime.isoformat(), "timeZone": timezone},
            "end":    {"dateTime": end_dt.isoformat(),         "timeZone": timezone},
            "colorId": "7",
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email",  "minutes": 24 * 60},
                    {"method": "popup",  "minutes": 30},
                ],
            },
        }

        created = service.events().insert(calendarId="primary", body=body).execute()
        logger.info("Calendar event created: %s", created["id"])
        return {
            "success":    True,
            "event_id":   created["id"],
            "event_link": created.get("htmlLink", ""),
            "title":      title,
            "start":      start_datetime.isoformat(),
        }

    except (FileNotFoundError, RuntimeError) as e:
        status = check_calendar_auth()
        return {
            "success":  False,
            "error":    str(e),
            "status":   status.get("status"),
            "auth_url": status.get("auth_url"),
            "message":  "Connect Google Calendar first.",
        }
    except Exception as e:
        logger.error("Calendar event creation failed: %s", e)
        return {"success": False, "error": str(e), "message": "Could not create event."}


def create_study_deadline(task: str, deadline: datetime, country: str = "", notes: str = "") -> dict:
    start = deadline.replace(hour=9, minute=0, second=0, microsecond=0)
    desc  = f"Study abroad deadline — {country}\n\n{notes}".strip()
    return create_calendar_event(f"[udaan] {task}", start, desc, 30)


def bulk_create_timeline_events(events: list[dict]) -> list[dict]:
    results = []
    for ev in events:
        try:
            date_str = ev.get("date", "")
            if not date_str:
                results.append({"success": False, "error": "No date", "title": ev.get("title", "")})
                continue
            dt = datetime.fromisoformat(date_str) if "T" in date_str else \
                 datetime.strptime(date_str, "%Y-%m-%d").replace(hour=9, minute=0)
            results.append(create_calendar_event(
                title=ev.get("title", "Study Abroad Task"),
                start_datetime=dt,
                description=ev.get("description", ""),
                duration_minutes=ev.get("duration_minutes", 30),
            ))
        except Exception as e:
            results.append({"success": False, "error": str(e), "title": ev.get("title", "")})
    return results
