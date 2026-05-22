# tools/saver.py

from datetime import datetime
from db.supabase_client import insert_session, update_session
from tools.blacklist import add_to_seen
from config.settings import MAX_VALID_FINAL, MIN_VALID_FINAL


# ─────────────────────────────────────
# SAUVEGARDE SESSION
# ─────────────────────────────────────

async def save_session(session: dict) -> bool:
    """
    Sauvegarde la session dans Supabase
    """
    try:
        await insert_session(session)
        print(f"[Saver] Session {session['session_id']} sauvegardée ✅")
        return True
    except Exception as e:
        print(f"[Saver] Erreur sauvegarde session : {e}")
        return False


async def close_session(
    session_id: str,
    status: str,
    started_at: datetime,
    stats: dict
):
    """
    Ferme et met à jour la session avec les stats finales
    """
    ended_at = datetime.utcnow()
    duration = (ended_at - started_at).total_seconds() / 60

    await update_session(session_id, {
        "ended_at":         ended_at.isoformat(),
        "duration_minutes": round(duration, 2),
        "status":           status,
        **stats
    })

    print(
        f"[Saver] Session fermée → "
        f"status={status} | durée={round(duration, 2)}min"
    )


# ─────────────────────────────────────
# SÉLECTION TOP 15
# ─────────────────────────────────────

def select_top_prospects(scored_profiles: list[dict]) -> list[dict]:
    """
    Trie par score et sélectionne les meilleurs
    Min : 5 | Max : 15
    """
    # Déjà trié par GLM mais on re-trie par sécurité
    sorted_profiles = sorted(
        scored_profiles,
        key=lambda x: x["score_total"],
        reverse=True
    )

    top = sorted_profiles[:MAX_VALID_FINAL]

    print(f"[Saver] TOP {len(top)} prospects sélectionnés")
    return top


# ─────────────────────────────────────
# SAUVEGARDE PROSPECTS + VALIDATION
# ─────────────────────────────────────

async def save_top_prospects(
    scored_profiles: list[dict],
    session_id: str
) -> dict:
    """
    Vérifie le minimum requis
    Sauvegarde les TOP prospects dans Supabase
    Retourne le résultat final
    """

    # Sélection TOP 15
    top = select_top_prospects(scored_profiles)

    # Vérification minimum
    if len(top) < MIN_VALID_FINAL:
        print(
            f"[Saver] ❌ Insuffisant — "
            f"{len(top)} prospects / {MIN_VALID_FINAL} minimum requis"
        )
        return {
            "success":   False,
            "reason":    "insufficient_prospects",
            "count":     len(top),
            "prospects": []
        }

    # Sauvegarde chaque prospect dans Supabase
    saved = []
    for prospect in top:
        ok = await add_to_seen(prospect, session_id)
        if ok:
            saved.append(prospect)

    print(f"[Saver] {len(saved)} prospects sauvegardés en base ✅")

    return {
        "success":   True,
        "count":     len(saved),
        "prospects": saved
    }


# ─────────────────────────────────────
# FORMAT OUTPUT FINAL
# ─────────────────────────────────────

def format_output(prospects: list[dict]) -> list[dict]:
    """
    Formate les données pour l'utilisateur final
    Seulement les infos utiles pour la prospection manuelle
    """
    output = []

    for p in prospects:
        output.append({
            "username":     p.get("username"),
            "profile_url":  f"https://instagram.com/{p.get('username')}",
            "niche":        p.get("niche"),
            "followers":    p.get("followers"),
            "bio":          p.get("bio"),

            # Contact
            "contact": {
                "dm":       True,
                "whatsapp": p.get("has_whatsapp", False),
                "whatsapp_number": p.get("whatsapp_number")
            },

            # Score
            "score": {
                "total":    p.get("score_total"),
                "activite": p.get("score_activite"),
                "offre":    p.get("score_offre"),
                "douleur":  p.get("score_douleur"),
                "france":   p.get("score_france"),
                "raison":   p.get("glm_reason")
            },

            # Signaux
            "signaux": {
                "vend_via_dm":    p.get("sells_via_dm"),
                "a_whatsapp":     p.get("has_whatsapp"),
                "a_linktree":     p.get("has_linktree"),
                "a_vrai_site":    p.get("has_real_website"),
                "clients_visibles": p.get("has_customer_comments")
            },

            "source": p.get("source"),
            "status": "pending"
        })

    return output
