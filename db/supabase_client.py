# db/supabase_client.py

import httpx
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "return=representation"
}

BASE    = f"{SUPABASE_URL}/rest/v1"
TIMEOUT = httpx.Timeout(10.0, connect=5.0)


# ─────────────────────────────────────
# PROSPECTS
# ─────────────────────────────────────

async def insert_prospect(prospect: dict) -> dict:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.post(
                f"{BASE}/prospects_seen",
                headers=HEADERS,
                json=prospect
            )
            return r.json()
    except Exception as e:
        print(f"[Supabase] insert_prospect erreur : {e}")
        return {}


async def get_prospect(username: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(
                f"{BASE}/prospects_seen",
                headers=HEADERS,
                params={"username": f"eq.{username}"}
            )
            data = r.json()
            return data[0] if isinstance(data, list) and data else None
    except Exception as e:
        print(f"[Supabase] get_prospect erreur : {e}")
        return None


async def update_prospect_status(username: str, status: str):
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            await client.patch(
                f"{BASE}/prospects_seen",
                headers=HEADERS,
                params={"username": f"eq.{username}"},
                json={"status": status}
            )
    except Exception as e:
        print(f"[Supabase] update_prospect_status erreur : {e}")


async def get_all_prospects(status: str = None) -> list:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            params = {}
            if status:
                params["status"] = f"eq.{status}"
            r = await client.get(
                f"{BASE}/prospects_seen",
                headers=HEADERS,
                params=params
            )
            data = r.json()
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[Supabase] get_all_prospects erreur : {e}")
        return []


# ─────────────────────────────────────
# SESSIONS
# ─────────────────────────────────────

async def insert_session(session: dict) -> dict:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.post(
                f"{BASE}/sessions",
                headers=HEADERS,
                json=session
            )
            return r.json()
    except Exception as e:
        print(f"[Supabase] insert_session erreur : {e}")
        return {}


async def update_session(session_id: str, data: dict):
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            await client.patch(
                f"{BASE}/sessions",
                headers=HEADERS,
                params={"session_id": f"eq.{session_id}"},
                json=data
            )
    except Exception as e:
        print(f"[Supabase] update_session erreur : {e}")


async def get_sessions_last_4h() -> list:
    try:
        from datetime import datetime, timedelta
        cutoff = (
            datetime.utcnow() - timedelta(hours=4)
        ).isoformat()

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(
                f"{BASE}/sessions",
                headers=HEADERS,
                params={
                    "status":     "eq.success",
                    "started_at": f"gte.{cutoff}"
                }
            )
            data = r.json()
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[Supabase] get_sessions_last_4h erreur : {e}")
        return []


async def get_session(session_id: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(
                f"{BASE}/sessions",
                headers=HEADERS,
                params={"session_id": f"eq.{session_id}"}
            )
            data = r.json()
            return data[0] if isinstance(data, list) and data else None
    except Exception as e:
        print(f"[Supabase] get_session erreur : {e}")
        return None
