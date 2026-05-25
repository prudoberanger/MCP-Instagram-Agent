# routes/mcp_tools.py

from flask import Blueprint, request, jsonify
from datetime import datetime
import asyncio
import uuid

from tools.quota import quota_manager
from tools.fetcher import fetch_all_sources
from tools.enricher import enrich_all_profiles
from tools.blacklist import filter_blacklisted
from tools.webhook_quota import check_all_keys, SERVICE_STATUS, get_services_summary
from tools.saver import (
    save_session,
    save_top_prospects,
    close_session,
    format_output
)
from config.settings import NICHES, RAPIDAPI_KEY
from security.auth import require_api_key
from security.rate_limit import rate_limit

mcp = Blueprint("mcp", __name__)


def run(coro):
    return asyncio.run(coro)


# ─────────────────────────────────────
# GET /mcp/quota
# ─────────────────────────────────────

@mcp.route("/quota", methods=["GET"])
@require_api_key
@rate_limit
def check_quota():
    status = run(quota_manager.get_status())
    return jsonify(status)


# ─────────────────────────────────────
# GET /mcp/niches
# ─────────────────────────────────────

@mcp.route("/niches", methods=["GET"])
@require_api_key
def get_niches():
    return jsonify({
        "niches": [
            {"key": key, "label": value["label"]}
            for key, value in NICHES.items()
        ]
    })


# ─────────────────────────────────────
# GET /mcp/keys/status
# ─────────────────────────────────────

@mcp.route("/keys/status", methods=["GET"])
@require_api_key
def keys_status():
    return jsonify({
        "services":   get_services_summary(),
        "keys_count": 1
    })


# ─────────────────────────────────────
# POST /mcp/keys/check
# ─────────────────────────────────────

@mcp.route("/keys/check", methods=["POST"])
@require_api_key
@rate_limit
def check_keys():
    result = run(check_all_keys())
    return jsonify(result)


# ─────────────────────────────────────
# POST /mcp/run-session
# ─────────────────────────────────────

@mcp.route("/run-session", methods=["POST"])
@require_api_key
@rate_limit
def run_session():
    data  = request.get_json()
    niche = data.get("niche") if data else None

    if not niche or niche not in NICHES:
        return jsonify({
            "error": f"Niche invalide. Disponibles : {list(NICHES.keys())}"
        }), 400

    # Vérif quota
    try:
        run(quota_manager.guard())
    except PermissionError as e:
        return jsonify({"error": str(e)}), 429

    session_id = str(uuid.uuid4())
    started_at = datetime.utcnow()

    run(save_session({
        "session_id": session_id,
        "niche":      niche,
        "started_at": started_at.isoformat(),
        "status":     "running"
    }))

    try:
        # ÉTAPE 1 — Collecte
        print(f"\n[Pipeline] ÉTAPE 1 — Collecte niche : {niche}")
        raw_profiles = run(fetch_all_sources(niche))

        if not raw_profiles:
            run(close_session(session_id, "insufficient", started_at, {
                "error_message": "Aucun profil collecté"
            }))
            return jsonify({"error": "Aucun profil trouvé"}), 404

        # ÉTAPE 2 — Blacklist
        print("[Pipeline] ÉTAPE 2 — Vérification blacklist...")
        fresh = run(filter_blacklisted(raw_profiles))

        if not fresh:
            run(close_session(session_id, "insufficient", started_at, {
                "error_message": "Tous les profils déjà vus"
            }))
            return jsonify({"error": "Tous déjà prospectés"}), 404

        for p in fresh:
            p["niche"]      = niche
            p["session_id"] = session_id

        # ÉTAPE 3 — Enrichissement
        print("[Pipeline] ÉTAPE 3 — Enrichissement profils...")
        enriched = run(enrich_all_profiles(fresh))

        if not enriched:
            run(close_session(session_id, "insufficient", started_at, {
                "error_message": "Aucun profil valide après enrichissement"
            }))
            return jsonify({
                "error": "Aucun profil valide après enrichissement"
            }), 404

        # ÉTAPE 4 — Filtre (bypass temporaire)
        print("[Pipeline] ÉTAPE 4 — Filtre bypass...")
        filtered = enriched

        # ÉTAPE 5 — Scoring temporaire
        print("[Pipeline] ÉTAPE 5 — Scoring...")
        for p in filtered:
            is_active = p.get("is_active", False)
            is_french = p.get("is_french", False)
            has_wa    = p.get("has_whatsapp", False)
            sells_dm  = p.get("sells_via_dm", False)
            has_site  = p.get("has_real_website", False)

            score_activite = 15 if is_active else 5
            score_offre    = 15 if sells_dm or has_wa else 8
            score_douleur  = 20 if not has_site else 10
            score_france   = 20 if is_french else 5

            p["score_total"]    = score_activite + score_offre + score_douleur + score_france
            p["score_activite"] = score_activite
            p["score_offre"]    = score_offre
            p["score_douleur"]  = score_douleur
            p["score_france"]   = score_france
            p["glm_reason"]     = "Score automatique — IA activée prochainement"

        scored = sorted(
            filtered,
            key=lambda x: x["score_total"],
            reverse=True
        )

        # ÉTAPE 6 — Sauvegarde TOP
        print("[Pipeline] ÉTAPE 6 — Sauvegarde...")
        result = run(save_top_prospects(scored, session_id))

        if not result["success"]:
            run(close_session(session_id, "insufficient", started_at, {
                "total_delivered": result["count"]
            }))
            return jsonify({
                "error": f"Seulement {result['count']} prospects. Minimum : 5"
            }), 404

        run(close_session(session_id, "success", started_at, {
            "total_fetched":   len(raw_profiles),
            "total_delivered": result["count"]
        }))

        output = format_output(result["prospects"])
        print(f"\n[Session] ✅ {result['count']} prospects livrés")

        return jsonify({
            "session_id": session_id,
            "niche":      NICHES[niche]["label"],
            "total":      result["count"],
            "prospects":  output
        })

    except Exception as e:
        run(close_session(session_id, "error", started_at, {
            "error_message": str(e)
        }))
        return jsonify({"error": f"Erreur pipeline : {e}"}), 500


# ─────────────────────────────────────
# PATCH /mcp/prospect/status
# ─────────────────────────────────────

@mcp.route("/prospect/status", methods=["PATCH"])
@require_api_key
def update_status():
    data     = request.get_json()
    username = data.get("username")
    status   = data.get("status")

    if status not in ["prospected", "rejected"]:
        return jsonify({
            "error": "Status invalide : prospected | rejected"
        }), 400

    from tools.blacklist import mark_as_prospected, mark_as_rejected
    if status == "prospected":
        run(mark_as_prospected(username))
    else:
        run(mark_as_rejected(username))

    return jsonify({
        "username": username,
        "status":   status,
        "updated":  True
    })


# ─────────────────────────────────────
# GET /mcp/prospects
# ─────────────────────────────────────

@mcp.route("/prospects", methods=["GET"])
@require_api_key
@rate_limit
def get_prospects():
    status    = request.args.get("status")
    from db.supabase_client import get_all_prospects
    prospects = run(get_all_prospects(status))
    return jsonify({
        "total":     len(prospects),
        "prospects": prospects
    })


# ─────────────────────────────────────
# GET /mcp/sessions
# ─────────────────────────────────────

@mcp.route("/sessions", methods=["GET"])
@require_api_key
def get_sessions():
    from db.supabase_client import get_sessions_last_4h
    sessions = run(get_sessions_last_4h())
    return jsonify({
        "total":    len(sessions),
        "sessions": sessions
    })
