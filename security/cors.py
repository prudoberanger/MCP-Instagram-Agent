# security/cors.py

import os

ALLOWED_ORIGINS = [
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
    "https://ton-dashboard.vercel.app"
]

def get_cors_config():
    return {
        "origins":     ALLOWED_ORIGINS,
        "methods":     ["GET", "POST", "PATCH", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-API-Key", "Authorization"]
    }
