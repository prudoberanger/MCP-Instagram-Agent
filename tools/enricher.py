# tools/enricher.py

import asyncio
import random
import httpx
import re
from config.settings import (
    RAPIDAPI_KEY,
    LOOTER_HOST,
    PLAYWRIGHT_HOST,
    SCRAPER21_HOST,
    URLMETA_HOST,
    SIGNALS_DM,
    SIGNALS_WHATSAPP,
    SIGNALS_CUSTOMER,
    MIN_FOLLOWERS,
    MAX_FOLLOWERS
)
from tools.webhook_quota import (
    is_quota_exceeded,
    is_service_active,
    mark_service_exhausted
)

TIMEOUT = httpx.Timeout(30.0, connect=5.0)


# ─────────────────────────────────────
# HELPERS
# ─────────────────────────────────────

def detect_signals(text: str, signals: list) -> bool:
    if not text:
        return False
    return any(s.lower() in text.lower() for s in signals)


def extract_whatsapp_number(text: str) -> str | None:
    if not text:
        return None
    match = re.search(r"wa\.me/(\+?\d{10,15})", text)
    return match.group(1) if match else None


def get_headers(host: str) -> dict:
    return {
        "x-rapidapi-host": host,
        "x-rapidapi-key":  RAPIDAPI_KEY,
        "Content-Type":    "application/json"
    }


# ─────────────────────────────────────
# LOOTER /profile — infos profil
# ─────────────────────────────────────

async def get_profile_looter(username: str) -> dict:
    """
    Récupère infos profil via Looter /profile
    Retourne directement à la racine du JSON
    """
    if not is_service_active("looter"):
        print(f"[Looter/Profile] Service désactivé")
        return {}

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(
                f"https://{LOOTER_HOST}/profile",
                headers=get_headers(LOOTER_HOST),
                params={"username": username}
            )
            data = r.json()

            if is_quota_exceeded(str(data)):
                print(f"[Looter/Profile] Quota épuisé → change clé dans .env")
                mark_service_exhausted("looter")
                return {}

            print(f"[Looter/Profile] ✅ @{username}")
            return data

    except httpx.ConnectTimeout:
        print(f"[Looter/Profile] Timeout @{username}")
        return {}
    except Exception as e:
        print(f"[Looter/Profile] Erreur @{username} : {e}")
        return {}


# ─────────────────────────────────────
# PLAYWRIGHT — scraping signaux
# ─────────────────────────────────────

async def scrape_playwright(username: str) -> str:
    url = f"https://www.instagram.com/{username}/"

    if not is_service_active("playwright"):
        print(f"[Playwright] Désactivé → fallback scraper21")
        return await scrape_scraper21(username)

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(
                f"https://{PLAYWRIGHT_HOST}/api/scrape/text",
                headers=get_headers(PLAYWRIGHT_HOST),
                params={"url": url}
            )
            data = r.json()

            if is_quota_exceeded(str(data)):
                print(f"[Playwright] Quota épuisé → change clé dans .env")
                mark_service_exhausted("playwright")
                return await scrape_scraper21(username)

            if data.get("success"):
                print(f"[Playwright] ✅ @{username}")
                return data.get("text", "")
            return ""

    except httpx.ConnectTimeout:
        print(f"[Playwright] Timeout @{username} → fallback scraper21")
        return await scrape_scraper21(username)
    except Exception as e:
        print(f"[Playwright] Erreur @{username} : {e}")
        return await scrape_scraper21(username)


# ─────────────────────────────────────
# SCRAPER21 — fallback signaux
# ─────────────────────────────────────

async def scrape_scraper21(username: str) -> str:
    if not is_service_active("scraper21"):
        print(f"[Scraper21] Désactivé")
        return ""

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(
                f"https://{SCRAPER21_HOST}/api/v1/posts",
                headers=get_headers(SCRAPER21_HOST),
                params={"username": username}
            )
            data = r.json()

            if is_quota_exceeded(str(data)):
                print(f"[Scraper21] Quota épuisé → change clé dans .env")
                mark_service_exhausted("scraper21")
                return ""

            posts = data.get("data", {}).get("posts", [])
            text  = " ".join([
                p.get("caption", "") or ""
                for p in posts[:5]
            ])
            print(f"[Scraper21] ✅ @{username}")
            return text

    except httpx.ConnectTimeout:
        print(f"[Scraper21] Timeout @{username}")
        return ""
    except Exception as e:
        print(f"[Scraper21] Erreur @{username} : {e}")
        return ""


# ─────────────────────────────────────
# URLMETA — vérification site web
# ─────────────────────────────────────

async def check_website(url: str) -> dict:
    if not url or not is_service_active("urlmeta"):
        return {"valid": False, "type": "none"}

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.post(
                f"https://{URLMETA_HOST}/extract",
                headers=get_headers(URLMETA_HOST),
                json={"url": url, "render_js": False}
            )
            data = r.json()

            if is_quota_exceeded(str(data)):
                print(f"[URLMeta] Quota épuisé → change clé dans .env")
                mark_service_exhausted("urlmeta")
                return {"valid": False, "type": "unknown"}

            title       = data.get("title", "")
            description = data.get("description", "")

            if "linktr.ee" in url:
                site_type = "linktree"
            elif "beacons.ai" in url:
                site_type = "beacons"
            elif title or description:
                site_type = "real_website"
            else:
                site_type = "unknown"

            print(f"[URLMeta] ✅ {url} → {site_type}")
            return {
                "valid":       True,
                "type":        site_type,
                "title":       title,
                "description": description
            }

    except httpx.ConnectTimeout:
        print(f"[URLMeta] Timeout")
        return {"valid": False, "type": "timeout"}
    except Exception as e:
        print(f"[URLMeta] Erreur : {e}")
        return {"valid": False, "type": "error"}


# ─────────────────────────────────────
# ENRICHISSEMENT D'UN PROFIL
# ─────────────────────────────────────

async def enrich_profile(profile: dict) -> dict:
    username = profile["username"]

    try:
        # ÉTAPE 1 — Infos profil via Looter /profile
        data = await get_profile_looter(username)

        # Looter retourne directement à la racine
        bio       = data.get("biography", "") or ""
        ext_link  = data.get("external_url", "") or ""
        followers = (
            data.get("edge_followed_by", {}).get("count", 0) or
            data.get("follower_count", 0) or
            profile.get("followers", 0)
        )
        following = data.get("edge_follow", {}).get("count", 0) or 0
        posts_count = (
            data.get("edge_owner_to_timeline_media", {}).get("count", 0) or
            data.get("media_count", 0) or 0
        )
        full_name       = data.get("full_name", "") or ""
        is_professional = data.get("is_professional_account", False)
        is_business     = data.get("is_business_account", False)

        # ÉTAPE 2 — Scraping signaux via Playwright
        scraped_text = await scrape_playwright(username)

        # ÉTAPE 3 — Vérification site web via URLMeta
        site_info = await check_website(ext_link) if ext_link else {
            "valid": False, "type": "none"
        }

        # Texte complet pour analyse
        full_text = f"{bio} {ext_link} {full_name} {scraped_text}"

        # Signaux commerciaux
        sells_via_dm          = detect_signals(full_text, SIGNALS_DM)
        has_whatsapp          = detect_signals(full_text, SIGNALS_WHATSAPP)
        has_linktree          = "linktr.ee" in full_text.lower()
        has_beacons           = "beacons.ai" in full_text.lower()
        has_real_website      = site_info.get("type") == "real_website"
        has_customer_comments = detect_signals(full_text, SIGNALS_CUSTOMER)
        whatsapp_number       = extract_whatsapp_number(full_text)
        phone_in_bio          = re.findall(
            r"📞?\s*0[1-9][\d\s]{8,}", bio
        )

        # France
        france_signals = [
            "france", "paris", "lyon", "marseille",
            "toulouse", "bordeaux", "lille", "nice",
            "nantes", "strasbourg", "🇫🇷", ".fr"
        ]
        is_french = detect_signals(full_text, france_signals)

        # Validation
        followers_valid = MIN_FOLLOWERS <= followers <= MAX_FOLLOWERS
        is_active       = (
            posts_count > 0 or
            is_professional or
            is_business
        )

        await asyncio.sleep(random.uniform(2.0, 4.0))

        print(
            f"[Enricher] @{username} → "
            f"{followers} followers | "
            f"FR:{is_french} | "
            f"DM:{sells_via_dm} | "
            f"WA:{has_whatsapp} | "
            f"Site:{site_info.get('type')} | "
            f"valid:{followers_valid}"
        )

        return {
            **profile,
            "full_name":             full_name,
            "bio":                   bio,
            "external_link":         ext_link,
            "followers":             followers,
            "following":             following,
            "posts_count":           posts_count,
            "followers_valid":       followers_valid,
            "is_active":             is_active,
            "is_french":             is_french,
            "sells_via_dm":          sells_via_dm,
            "has_whatsapp":          has_whatsapp,
            "has_linktree":          has_linktree,
            "has_beacons":           has_beacons,
            "has_real_website":      has_real_website,
            "site_type":             site_info.get("type"),
            "site_title":            site_info.get("title"),
            "has_customer_comments": has_customer_comments,
            "whatsapp_number":       whatsapp_number,
            "phone_in_bio":          phone_in_bio,
            "is_professional":       is_professional,
            "is_business":           is_business,
            "enriched":              True
        }

    except Exception as e:
        print(f"[Enricher] Erreur @{username} : {e}")
        return {**profile, "enriched": False}


# ─────────────────────────────────────
# ENRICHISSEMENT DE TOUS LES PROFILS
# ─────────────────────────────────────

async def enrich_all_profiles(profiles: list[dict]) -> list[dict]:
    enriched = []

    for i, profile in enumerate(profiles):
        print(f"[Enricher] {i+1}/{len(profiles)} → @{profile['username']}")
        result = await enrich_profile(profile)
        enriched.append(result)

    valid = [
        p for p in enriched
        if p.get("enriched")
        and p.get("followers_valid")
        and p.get("is_active")
    ]

    print(f"[Enricher] {len(valid)}/{len(profiles)} profils valides")
    return valid
