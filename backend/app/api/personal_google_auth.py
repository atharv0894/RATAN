"""
Google OAuth 2.0 for Personal Users ONLY.

Flow:
  1. Frontend redirects to GET /api/v1/personal/auth/google
     → backend builds Google authorization URL and returns it
  2. Google redirects back to GET /api/v1/personal/auth/google/callback?code=...
     → backend exchanges code for tokens, upserts user, returns JWT
  3. POST /api/v1/personal/auth/google/mobile  (for SPA/PKCE flows)
     → frontend sends the Google id_token, backend verifies and returns JWT
"""
import os
import uuid
import time
import secrets

import requests
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from pydantic import BaseModel

from app.services.auth_service import AuthService
from app.services.session_service import SessionService
from app.api.responses import APISuccessResponse
from app.database.tidb import get_tidb_connection

router = APIRouter()

# ─── Config ────────────────────────────────────────────────────────────────────
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/personal/auth/google/callback")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

# In-memory CSRF state store (for a single-instance server; use Redis in HA)
_pending_states: dict[str, float] = {}


def _build_jwt_for_user(user: dict, request_ip: str = "unknown", user_agent: str = "google-oauth") -> dict:
    """Issue access + refresh tokens for a verified user row."""
    payload = {
        "sub": user["id"],
        "account_type": "PERSONAL",
        "email": user["email"],
        "full_name": user["full_name"],
        "org_id": None,
        "plant_id": None,
        "department_id": None,
        "role": None,
    }
    access_token = AuthService.create_access_token(data=payload)
    refresh_token = AuthService.create_refresh_token(data={"sub": user["id"]})
    SessionService.create_session(user["id"], refresh_token, request_ip, user_agent)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


def _upsert_google_user(google_info: dict) -> dict:
    """
    Upsert a Personal user from Google profile data.
    Returns the full user row dict.
    """
    email: str = google_info["email"]
    google_id: str = google_info["sub"]
    full_name: str = google_info.get("name", email.split("@")[0])
    picture: str = google_info.get("picture", "")

    conn = get_tidb_connection()
    cursor = conn.cursor()
    now = time.time()

    try:
        # 1. Look up by google_id first (returning user)
        cursor.execute(
            "SELECT id, email, full_name, account_type FROM users WHERE google_id = ? AND account_type = 'PERSONAL' AND is_deleted = 0",
            (google_id,),
        )
        user = cursor.fetchone()
        if user:
            # Update last login
            cursor.execute(
                "UPDATE users SET last_google_login = ?, profile_picture = ?, updated_at = ? WHERE id = ?",
                (now, picture, now, user["id"]),
            )
            conn.commit()
            return dict(user)

        # 2. Look up by email (account linking)
        cursor.execute(
            "SELECT id, email, full_name, account_type, provider FROM users WHERE email = ? AND account_type = 'PERSONAL' AND is_deleted = 0",
            (email,),
        )
        existing = cursor.fetchone()
        if existing:
            # Link Google to existing LOCAL account → also mark verified
            cursor.execute(
                """UPDATE users
                   SET google_id = ?, profile_picture = ?, provider = 'GOOGLE',
                       is_verified = 1, email_verified_at = ?,
                       last_google_login = ?, updated_at = ?
                   WHERE id = ?""",
                (google_id, picture, now, now, now, existing["id"]),
            )
            conn.commit()
            return dict(existing)

        # 3. Brand-new Google user → auto-create Personal account
        user_id = str(uuid.uuid4())
        cursor.execute(
            """INSERT INTO users
               (id, account_type, email, password_hash, full_name,
                provider, google_id, profile_picture, provider_account_id,
                is_verified, email_verified_at, last_google_login,
                created_at, updated_at)
               VALUES (?, 'PERSONAL', ?, '', ?, 'GOOGLE', ?, ?, ?, 1, ?, ?, ?, ?)""",
            (
                user_id, email, full_name,
                google_id, picture, google_id,
                now, now, now, now,
            ),
        )
        # Also create personal_settings row
        cursor.execute(
            "INSERT INTO personal_settings (id, user_id, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), user_id, now, now),
        )
        conn.commit()
        return {"id": user_id, "email": email, "full_name": full_name, "account_type": "PERSONAL"}

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


# ─── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/google")
def google_oauth_start():
    """Return the Google OAuth authorization URL for the frontend to redirect to."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured on this server.")

    state = secrets.token_urlsafe(32)
    _pending_states[state] = time.time()

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
        "state": state,
    }
    from urllib.parse import urlencode
    url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return APISuccessResponse(data={"url": url})


@router.get("/google/callback")
def google_oauth_callback(code: str = Query(...), state: str = Query(...)):
    """
    Google redirects here after the user grants permission.
    We exchange the code for tokens, upsert the user, issue our own JWT,
    and redirect the browser to the frontend with tokens in the URL fragment.
    """
    # CSRF check
    stored_time = _pending_states.pop(state, None)
    if stored_time is None or (time.time() - stored_time) > 600:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state.")

    # Exchange code for tokens
    token_resp = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    token_data = token_resp.json()
    if "error" in token_data:
        raise HTTPException(status_code=400, detail=f"Google token error: {token_data['error']}")

    # Fetch user info
    userinfo_resp = requests.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
        timeout=10,
    )
    google_info = userinfo_resp.json()
    if not google_info.get("email_verified"):
        raise HTTPException(status_code=400, detail="Google account email is not verified.")

    user = _upsert_google_user(google_info)
    tokens = _build_jwt_for_user(user)

    # Redirect to frontend callback page with tokens in fragment
    redirect_url = (
        f"{FRONTEND_URL}/personal/google-callback"
        f"#access_token={tokens['access_token']}"
        f"&refresh_token={tokens['refresh_token']}"
    )
    return RedirectResponse(url=redirect_url)


class GoogleMobileRequest(BaseModel):
    """For SPA / mobile: frontend sends the Google id_token directly."""
    id_token: str


@router.post("/google/mobile", response_model=APISuccessResponse)
def google_oauth_mobile(payload: GoogleMobileRequest):
    """
    Verify a Google ID token issued by the frontend (e.g., Google One Tap / GSI).
    Returns our own JWT.
    """
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured on this server.")
    try:
        idinfo = google_id_token.verify_oauth2_token(
            payload.id_token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10,
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {e}")

    if not idinfo.get("email_verified"):
        raise HTTPException(status_code=400, detail="Google account email is not verified.")

    user = _upsert_google_user(idinfo)
    tokens = _build_jwt_for_user(user)
    return APISuccessResponse(data=tokens)
