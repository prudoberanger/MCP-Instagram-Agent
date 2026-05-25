# security/auth.py

import os
import hashlib
from flask import request, jsonify
from functools import wraps

MCP_SECRET_KEY = os.getenv("MCP_SECRET_KEY")

def require_api_key(f):
    """
    Décorateur — vérifie la clé API
    Toutes les routes MCP doivent l'utiliser
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = (
            request.headers.get("X-API-Key") or
            request.headers.get("Authorization", "").replace("Bearer ", "")
        )

        if not api_key:
            return jsonify({
                "error": "Clé API manquante"
            }), 401

        if api_key != MCP_SECRET_KEY:
            return jsonify({
                "error": "Clé API invalide"
            }), 403

        return f(*args, **kwargs)
    return decorated
