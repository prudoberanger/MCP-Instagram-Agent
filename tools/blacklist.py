# tools/blacklist.py

from db.supabase_client import get_prospect, insert_prospect, update_prospect_status


# ─────────────────────────────────────
# VÉRIFICATION BLACKLIST
# ─────────────────────────────────────

async def is_blacklisted(username: str) -> bool:
    """
    Vérifie si un username a déjà été vu
    Peu importe son statut (pending, prospected, rejected)
    """
    prospect = await get_prospect(username)
    
    if prospect:
        print(f"[Blacklist] @{username} déjà dans la base → skip")
        return True
    
    return False


# ─────────────────────────────────────
# FILTRE BATCH — vérifie tous les profils
# ─────────────────────────────────────

async def filter_blacklisted(profiles: list[dict]) -> list[dict]:
    """
    Filtre les profils déjà vus dans Supabase
    Appelé AVANT Playwright pour ne pas perdre de temps
    """
    fresh = []

    for profile in profiles:
        username = profile["username"]
        already_seen = await is_blacklisted(username)
        
        if not already_seen:
            fresh.append(profile)

    print(
        f"[Blacklist] {len(fresh)}/{len(profiles)} "
        f"profils nouveaux après vérification"
    )
    return fresh


# ─────────────────────────────────────
# AJOUT EN BASE
# ─────────────────────────────────────

async def add_to_seen(profile: dict, session_id: str) -> bool:
    """
    Ajoute un prospect validé dans Supabase
    Status initial : pending
    """
    try:
        await insert_prospect({
            "username":         profile.get("username"),
            "full_name":        profile.get("full_name"),
            "bio":              profile.get("bio"),
            "niche":            profile.get("niche"),
            "followers":        profile.get("followers", 0),
            "score_total":      profile.get("score_total", 0),
            "score_activite":   profile.get("score_activite", 0),
            "score_offre":      profile.get("score_offre", 0),
            "score_douleur":    profile.get("score_douleur", 0),
            "score_france":     profile.get("score_france", 0),
            "glm_reason":       profile.get("glm_reason"),
            "has_whatsapp":     profile.get("has_whatsapp", False),
            "sells_via_dm":     profile.get("sells_via_dm", False),
            "has_real_website": profile.get("has_real_website", False),
            "external_link":    profile.get("external_link"),
            "source":           profile.get("source"),
            "session_id":       session_id,
            "status":           "pending"
        })
        print(f"[Blacklist] @{profile['username']} ajouté en base ✅")
        return True

    except Exception as e:
        print(f"[Blacklist] Erreur ajout @{profile['username']} : {e}")
        return False


# ─────────────────────────────────────
# MISE À JOUR STATUT
# ─────────────────────────────────────

async def mark_as_prospected(username: str):
    """Marque un prospect comme contacté manuellement"""
    await update_prospect_status(username, "prospected")
    print(f"[Blacklist] @{username} marqué comme prospecté ✅")


async def mark_as_rejected(username: str):
    """Marque un prospect comme rejeté"""
    await update_prospect_status(username, "rejected")
    print(f"[Blacklist] @{username} marqué comme rejeté ❌")
