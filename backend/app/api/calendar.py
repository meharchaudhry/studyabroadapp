"""
Google Calendar API endpoints
==============================
  GET  /calendar/status           — check auth state
  GET  /calendar/connect          — get OAuth URL → redirect user to Google
  GET  /calendar/callback         — Google redirects here with ?code=...
  GET  /calendar/disconnect       — revoke token
  POST /calendar/create-event     — create a single event
  POST /calendar/bulk-create      — create multiple events
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

FRONTEND_URL = "http://localhost:5173"


# ── Request models ─────────────────────────────────────────────────────────────

class CalendarEventRequest(BaseModel):
    title: str
    start_datetime: str          # ISO: "2025-09-01T10:00:00"
    description: Optional[str]  = ""
    duration_minutes: Optional[int] = 60
    location: Optional[str]     = ""
    timezone: Optional[str]     = "Asia/Kolkata"


class BulkCalendarRequest(BaseModel):
    events: list[dict]


# ── Auth endpoints ─────────────────────────────────────────────────────────────

@router.get("/status")
def calendar_status(current_user: User = Depends(get_current_user)) -> Any:
    """Return current Google Calendar connection state."""
    from app.services.calendar_service import check_calendar_auth
    return check_calendar_auth()


@router.get("/connect")
def calendar_connect(current_user: User = Depends(get_current_user)) -> Any:
    """Return the Google OAuth URL for the user to visit."""
    from app.services.calendar_service import get_auth_url, credentials_exist
    if not credentials_exist():
        raise HTTPException(
            status_code=503,
            detail="Google credentials not configured on server. Add google_credentials.json to backend/data/.",
        )
    try:
        url = get_auth_url()
        return {"auth_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback")
def calendar_callback(
    code: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
) -> HTMLResponse:
    """
    Google redirects here after the user approves.
    This endpoint does NOT require auth — Google sends the code here directly.
    After saving the token, redirect back to the frontend.
    """
    if error:
        return HTMLResponse(content=f"""
        <html><body style="font-family:sans-serif;text-align:center;padding:60px">
          <h2 style="color:#dc2626">Authorization denied</h2>
          <p>{error}</p>
          <a href="{FRONTEND_URL}" style="color:#1d4ed8">← Back to udaan</a>
        </body></html>
        """)

    if not code:
        return HTMLResponse(content=f"""
        <html><body style="font-family:sans-serif;text-align:center;padding:60px">
          <h2 style="color:#dc2626">No authorization code received</h2>
          <a href="{FRONTEND_URL}" style="color:#1d4ed8">← Back to udaan</a>
        </body></html>
        """)

    from app.services.calendar_service import exchange_code_for_token
    result = exchange_code_for_token(code)

    if result.get("success"):
        # Redirect back to frontend with success flag
        return HTMLResponse(content=f"""
        <html>
        <head><meta http-equiv="refresh" content="2;url={FRONTEND_URL}/appointments"></head>
        <body style="font-family:sans-serif;text-align:center;padding:60px;background:#f0fdf4">
          <div style="font-size:48px">✅</div>
          <h2 style="color:#16a34a">Google Calendar Connected!</h2>
          <p style="color:#166534">Your calendar is now linked to udaan. Redirecting you back…</p>
          <a href="{FRONTEND_URL}/appointments" style="color:#1d4ed8">Click here if not redirected</a>
        </body></html>
        """)
    else:
        return HTMLResponse(content=f"""
        <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#fef2f2">
          <div style="font-size:48px">❌</div>
          <h2 style="color:#dc2626">Authorization failed</h2>
          <p style="color:#991b1b">{result.get('error', 'Unknown error')}</p>
          <a href="{FRONTEND_URL}" style="color:#1d4ed8">← Back to udaan</a>
        </body></html>
        """)


@router.get("/disconnect")
def calendar_disconnect(current_user: User = Depends(get_current_user)) -> Any:
    """Revoke the stored OAuth token."""
    from app.services.calendar_service import revoke_token
    return revoke_token()


# ── Event endpoints ────────────────────────────────────────────────────────────

@router.post("/create-event")
def create_event(
    req: CalendarEventRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    from app.services.calendar_service import create_calendar_event
    try:
        start = datetime.fromisoformat(req.start_datetime)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid datetime. Use ISO 8601 e.g. 2025-09-01T10:00:00")

    return create_calendar_event(
        title=req.title,
        start_datetime=start,
        description=req.description or "",
        duration_minutes=req.duration_minutes or 60,
        location=req.location or "",
        timezone=req.timezone or "Asia/Kolkata",
    )


@router.post("/bulk-create")
def bulk_create_events(
    req: BulkCalendarRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    from app.services.calendar_service import bulk_create_timeline_events
    if not req.events:
        raise HTTPException(status_code=422, detail="events list cannot be empty")
    results = bulk_create_timeline_events(req.events)
    success = sum(1 for r in results if r.get("success"))
    return {"total": len(results), "success": success, "failed": len(results) - success, "results": results}
