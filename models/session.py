# models/session.py

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

class Session(BaseModel):
    
    # ─────────────────────────
    # IDENTITÉ
    # ─────────────────────────
    session_id: str = str(uuid.uuid4())
    niche: str
    
    # ─────────────────────────
    # TIMING
    # ─────────────────────────
    started_at: datetime = datetime.now()
    ended_at: Optional[datetime] = None
    duration_minutes: float = 0.0
    
    # ─────────────────────────
    # STATS SOURCES
    # ─────────────────────────
    looter_fetched: int = 0
    google_fetched: int = 0
    playwright_fetched: int = 0
    total_fetched: int = 0            # max 90
    total_after_dedupe: int = 0
    total_after_blacklist: int = 0
    
    # ─────────────────────────
    # RÉSULTATS PIPELINE
    # ─────────────────────────
    total_valid_qwen: int = 0
    total_scored_glm: int = 0
    total_delivered: int = 0          # 5-15 final
    
    # ─────────────────────────
    # STATUT
    # ─────────────────────────
    status: str = "running"
    # "running" | "success" | "insufficient" | "error"
    
    error_message: Optional[str] = None
    
    # ─────────────────────────
    # OUTPUT
    # ─────────────────────────
    top_prospects: List[str] = []     # liste des usernames TOP 15
