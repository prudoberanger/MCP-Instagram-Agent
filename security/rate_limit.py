# security/rate_limit.py

import time
from collections import defaultdict
from flask import request, jsonify
from functools import wraps

# Stockage en mémoire
REQUEST_COUNTS = defaultdict(list)

# Limites
MAX_REQUESTS = 10       # max requêtes
WINDOW_SECONDS = 60     # par minute


def rate_limit(f):
    """
    Décorateur — limite les requêtes par IP
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        ip  = request.remote_addr
        now = time.time()

        # Nettoie les anciennes requêtes
        REQUEST_COUNTS[ip] = [
            t for t in REQUEST_COUNTS[ip]
            if now - t < WINDOW_SECONDS
        ]

        if len(REQUEST_COUNTS[ip]) >= MAX_REQUESTS:
            return jsonify({
                "error": f"Trop de requêtes. Max {MAX_REQUESTS}/minute"
            }), 429

        REQUEST_COUNTS[ip].append(now)
        return f(*args, **kwargs)
    return decorated
