# routes/mcp_tools.py

from flask import Blueprint, request, jsonify
from datetime import datetime
import asyncio
import uuid

from tools.quota import quota_manager
from tools.fetcher import fetch_all_sources
from tools.enricher import enrich_all_profiles
from tools.filter_qwen import filter_all_profiles
from tools.scorer_glm import score_all_profiles
from tools.blacklist import filter_blacklisted
from tools.webhook_quota import check_all_keys, SERVICE_STATUS, get_services_summary
from tools.saver import (
    save_session,
    save_top_prospects,
    close_session,
    format_output
)
from config.settings import NICHES, RAPIDAPI_KEY

mcp = Blueprint("mcp", __name__)


def run(coro):
    return asyncio.run(coro)


# ─────────────────────────────────────
# GET /mcp/quota
# ─────────────────────────────────────

@mcp.route("/quota", methods=["GET"])
def check_quota():
    status = run(quota_manager.get_status())
    return jsonify(status)


# ─────────────────────────────────────
# GET /mcp/niches
# ─────────────────────────────────────

@mcp.route("/niches", methods=["GET"])
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
def keys_status():
    return jsonify({
        "services": get_services_summary(),
        "keys_count": len(RAPIDAPI_KEYS)
    })


# ─────────────────────────────────────
# POST /mcp/keys/check
# ─────────────────────────────────────

@mcp.route("/keys/check", methods=["POST"])
def check_keys():
    result = run(check_all_keys())
    return jsonify(result)


# ─────────────────────────────────────
# POST /mcp/run-session
# ─────────────────────────────────────

@mcp.route("/run-session", methods=["POST"])
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

        # ÉTAPE 4 — Filtre Qwen
        print("[Pipeline] ÉTAPE 4 — Filtre Qwen...")
        filtered = run(filter_all_profiles(enriched))

        if not filtered:
            run(close_session(session_id, "insufficient", started_at, {
                "error_message": "Aucun profil validé par Qwen"
            }))
            return jsonify({"error": "Aucun profil validé par Qwen"}), 404

        # ÉTAPE 5 — Scoring GLM
        print("[Pipeline] ÉTAPE 5 — Scoring GLM...")
        scored = run(score_all_profiles(filtered))

        # ÉTAPE 6 — Sauvegarde TOP
        print("[Pipeline] ÉTAPE 6 — Sauvegarde TOP prospects...")
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
        print(f"\n[Session] ✅ Terminée — {result['count']} prospects livrés")

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
def get_prospects():
    status    = request.args.get("status")
    from db.supabase_client import get_all_prospects
    prospects = run(get_all_prospects(status))
    return jsonify({
        "total":     len(prospects),
        "prospects": prospects
    })
