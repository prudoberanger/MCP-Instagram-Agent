# tools/quota.py

from datetime import datetime, timedelta
from db.supabase_client import get_sessions_last_4h
from config.settings import WINDOW_HOURS


class QuotaManager:

    async def check_quota(self) -> dict:
        sessions = await get_sessions_last_4h()

        total_minutes_used = sum(
            s.get("duration_minutes", 0) for s in sessions
        )

        window_minutes    = WINDOW_HOURS * 60
        minutes_remaining = window_minutes - total_minutes_used
        allowed           = minutes_remaining > 0

        next_available = None
        if not allowed and sessions:
            oldest      = min(sessions, key=lambda s: s["started_at"])
            oldest_time = datetime.fromisoformat(oldest["started_at"])
            next_available = oldest_time + timedelta(hours=WINDOW_HOURS)

        return {
            "allowed":            allowed,
            "sessions_in_window": len(sessions),
            "minutes_used":       round(total_minutes_used, 1),
            "minutes_remaining":  round(max(minutes_remaining, 0), 1),
            "next_available":     next_available.isoformat() if next_available else None
        }

    async def get_status(self) -> dict:
        quota = await self.check_quota()

        if quota["allowed"]:
            hours   = int(quota["minutes_remaining"] // 60)
            mins    = int(quota["minutes_remaining"] % 60)
            message = f"Disponible — {hours}h{mins:02d} restantes"
        else:
            message = f"Bloque — disponible a {quota['next_available']}"

        return {**quota, "message": message}

    async def guard(self) -> None:
        status = await self.get_status()
        if not status["allowed"]:
            raise PermissionError(
                f"Quota 4h atteint. {status['message']}"
            )


quota_manager = QuotaManager()
