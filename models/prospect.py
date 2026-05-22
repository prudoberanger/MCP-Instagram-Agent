# models/prospect.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class Prospect(BaseModel):
    
    # ─────────────────────────
    # IDENTITÉ
    # ─────────────────────────
    id: str = str(uuid.uuid4())
    username: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    profile_url: str = ""
    
    # ─────────────────────────
    # MÉTRIQUES
    # ─────────────────────────
    followers: int = 0
    following: int = 0
    posts_count: int = 0
    engagement_rate: float = 0.0
    last_post_days: int = 999
    
    # ─────────────────────────
    # SIGNAUX COMMERCIAUX
    # (détectés par Playwright)
    # ─────────────────────────
    sells_via_dm: bool = False
    has_whatsapp: bool = False
    has_linktree: bool = False
    has_beacons: bool = False
    has_real_website: bool = False
    external_link: Optional[str] = None
    has_customer_comments: bool = False
    whatsapp_number: Optional[str] = None
    
    # ─────────────────────────
    # VALIDATION
    # ─────────────────────────
    followers_valid: bool = False     # 500-10000
    is_active: bool = False           # post < 30 jours
    is_public: bool = True
    is_french: bool = False           # France détectée
    
    # ─────────────────────────
    # FILTRE QWEN
    # ─────────────────────────
    qwen_valid: bool = False
    qwen_confidence: float = 0.0
    qwen_reason: Optional[str] = None
    
    # ─────────────────────────
    # SCORING GLM
    # ─────────────────────────
    score_total: int = 0              # /100
    score_activite: int = 0           # /25
    score_offre: int = 0              # /25
    score_douleur: int = 0            # /30
    score_france: int = 0             # /20
    glm_reason: Optional[str] = None
    
    # ─────────────────────────
    # NICHE
    # ─────────────────────────
    niche: Optional[str] = None
    source: Optional[str] = None      # "looter" | "google" | "playwright"
    
    # ─────────────────────────
    # META
    # ─────────────────────────
    session_id: str = ""
    collected_at: datetime = datetime.now()
    status: str = "pending"           # "pending" | "prospected" | "rejected"
