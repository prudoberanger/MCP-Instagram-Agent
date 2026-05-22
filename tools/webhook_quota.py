# tools/webhook_quota.py

import httpx
from config.settings import (
    RAPIDAPI_KEY,
    LOOTER_HOST,
    SCRAPER21_HOST,
    CHEAPEST_HOST,
    PLAYWRIGHT_HOST,
    URLMETA_HOST
)

# ─────────────────────────────────────
# MESSAGES DE QUOTA
# ─────────────────────────────────────

QUOTA_EXHAUSTED_MESSAGES = [
    "exceeded",
    "monthly",
    "upgrade your plan",
    "requests on your current plan",
]

RATE_LIMIT_MESSAGES = [
    "rate limit",
    "too many requests",
    "429",
]

# ─────────────────────────────────────
# ÉTAT DES SERVICES
# Une seule clé — changée manuellement
# ─────────────────────────────────────

SERVICE_STATUS = {
    "looter":     {"active": True},
    "cheapest":   {"active": True},
    "playwright": {"active": True},
    "scraper21":  {"active": True},
    "urlmeta":    {"active": True},
}

SERVICE_HOSTS = {
    "looter":     LOOTER_HOST,
    "cheapest":   CHEAPEST_HOST,
    "playwright": PLAYWRIGHT_HOST,
    "scraper21":  SCRAPER21_HOST,
    "urlmeta":    URLMETA_HOST,
}


# ─────────────────────────────────────
# HELPERS
# ─────────────────────────────────────

def is_quota_exceeded(text: str) -> bool:
    text_lower = text.lower()
    return any(msg in text_lower for msg in QUOTA_EXHAUSTED_MESSAGES)


def is_rate_limited(text: str) -> bool:
    text_lower = text.lower()
    return any(msg in text_lower for msg in RATE_LIMIT_MESSAGES)


def is_service_active(service: str) -> bool:
    return SERVICE_STATUS.get(service, {}).get("active", False)


def mark_service_exhausted(service: str):
    """
    Marque un service comme épuisé
    L'utilisateur devra changer la clé manuellement dans .env
    """
    SERVICE_STATUS[service]["active"] = False
    print(
        f"[Webhook] ⚠️ {service} — quota épuisé\n"
        f"[Webhook] → Change RAPIDAPI_KEY dans .env et relance"
    )


def get_services_summary() -> dict:
    return {
        service: {
            "active": state["active"]
        }
        for service, state in SERVICE_STATUS.items()
    }


# ─────────────────────────────────────
# VÉRIFICATION TOUTES LES CLÉS
# ─────────────────────────────────────

async def check_all_keys() -> dict:
    results = {}

    test_cases = {
        "looter": {
            "url":    f"https://{LOOTER_HOST}/search",
            "params": {"query": "test"},
            "method": "GET"
        },
        "cheapest": {
            "url":    f"https://{CHEAPEST_HOST}/api/v1/instagram/user/nike",
            "params": {},
            "method": "GET"
        },
        "playwright": {
            "url":    f"https://{PLAYWRIGHT_HOST}/api/scrape/metadata",
            "params": {"url": "https://www.instagram.com/nike/"},
            "method": "GET"
        },
        "scraper21": {
            "url":    f"https://{SCRAPER21_HOST}/api/v1/posts",
            "params": {"username": "nike"},
            "method": "GET"
        },
        "urlmeta": {
            "url":    f"https://{URLMETA_HOST}/extract",
            "params": {},
            "method": "POST",
            "json":   {"url": "https://www.instagram.com/nike/",
                       "render_js": False}
        },
    }

    async with httpx.AsyncClient(timeout=30) as client:
        for service, config in test_cases.items():
            try:
                host    = SERVICE_HOSTS[service]
                headers = {
                    "x-rapidapi-host": host,
                    "x-rapidapi-key":  RAPIDAPI_KEY,
                    "Content-Type":    "application/json"
                }

                if config["method"] == "POST":
                    r = await client.post(
                        config["url"],
                        headers=headers,
                        json=config.get("json", {})
                    )
                else:
                    r = await client.get(
                        config["url"],
                        headers=headers,
                        params=config.get("params", {})
                    )

                data = r.json()
                text = str(data)

                if is_quota_exceeded(text):
                    status = "exhausted"
                    SERVICE_STATUS[service]["active"] = False
                elif is_rate_limited(text):
                    status = "rate_limited"
                elif r.status_code == 200:
                    status = "active"
                    SERVICE_STATUS[service]["active"] = True
                else:
                    status = "unknown"

                print(
                    f"[Webhook] {service} → "
                    f"{'✅ active' if status == 'active' else f'⚠️ {status}'}"
                )
                results[service] = {"status": status}

            except httpx.ConnectTimeout:
                print(f"[Webhook] {service} → ⏱️ timeout (pas épuisé)")
                results[service] = {"status": "timeout"}

            except httpx.ReadTimeout:
                print(f"[Webhook] {service} → ⏱️ read timeout (pas épuisé)")
                results[service] = {"status": "timeout"}

            except Exception as e:
                print(f"[Webhook] {service} → ⚠️ {type(e).__name__} : {e}")
                results[service] = {"status": "error"}

    return {
        "key_used":        RAPIDAPI_KEY[:10] + "..." if RAPIDAPI_KEY else "None",
        "services":        results,
        "services_summary": get_services_summary()
    }
