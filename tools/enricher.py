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
# FILTRAGE FRANCE AVANCÉ
# ─────────────────────────────────────

FRANCE_CITIES = [
    "paris", "lyon", "marseille", "toulouse",
    "bordeaux", "lille", "nice", "nantes",
    "strasbourg", "montpellier", "rennes",
    "grenoble", "dijon", "angers", "reims",
    "toulon", "brest", "le havre", "metz",
    "nancy", "perpignan", "caen", "orléans",
    "rouen", "clermont", "saint-etienne",
    "île-de-france", "idf", "var", "paca",
    "bretagne", "normandie", "alsace",
    "occitanie", "nouvelle-aquitaine",
    "auvergne", "hauts-de-france",
    "provence", "alpes", "corse",
    "seine", "yvelines", "essonne",
    "val-de-marne", "val-d'oise",
    "hauts-de-seine", "seine-et-marne",
    "seine-saint-denis"
]

FRANCE_SIGNALS = [
    "france", "français", "française",
    "🇫🇷", ".fr", "made in france",
    "livraison france", "toute la france",
    "partout en france", "france métro",
    "métropole", "hexagone"
]

FRANCE_PHONES = [
    "+33", "0033",
    "06 ", "07 ", "06.", "07.",
    "06-", "07-", "06/", "07/",
    "01 ", "02 ", "03 ", "04 ", "05 "
]

FRANCE_EXCLUDE = [
    "algérie", "algeria", "alger", "oran",
    "maroc", "morocco", "casablanca", "rabat",
    "tunisie", "tunisia", "tunis",
    "sénégal", "dakar", "abidjan",
    "côte d'ivoire", "cameroun", "douala",
    "mali", "burkina", "guinée", "congo",
    "madagascar", "togo", "bénin",
    "belgique", "bruxelles", "liège",
    "suisse", "genève", "lausanne",
    "canada", "québec", "montreal",
    "haïti", "port-au-prince",
    "espagne", "spain", "madrid",
    "italie", "italy", "rome",
    "🇩🇿", "🇲🇦", "🇹🇳", "🇸🇳", "🇧🇪",
    "🇨🇭", "🇨🇦", "🇭🇹", "🇨🇲", "🇨🇮",
    "🇲🇱", "🇧🇫", "🇬🇳", "🇨🇬", "🇲🇬",
    "🇹🇬", "🇧🇯", "🇪🇸", "🇮🇹",
]


def detect_france(text: str) -> bool:
    text_lower = text.lower()

    # Signaux exclusion
    exclude_count = sum(
        1 for e in FRANCE_EXCLUDE
        if e.lower() in text_lower
    )
    if exclude_count > 0:
        return False

    # Signaux positifs
    city_count   = sum(1 for c in FRANCE_CITIES if c in text_lower)
    signal_count = sum(1 for s in FRANCE_SIGNALS if s.lower() in text_lower)
    phone_count  = sum(1 for p in FRANCE_PHONES if p in text)

    return (city_count + signal_count + phone_count) >= 1


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
    if not is_service_active("looter"):
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
                mark_service_exhausted("playwright")
                return await scrape_scraper21(username)
            if data.get("success"):
                print(f"[Playwright] ✅ @{username}")
                return data.get("text", "")
            return ""
    except httpx.ConnectTimeout:
        return await scrape_scraper21(username)
    except Exception as e:
        print(f"[Playwright] Erreur @{username} : {e}")
        return await scrape_scraper21(username)


# ─────────────────────────────────────
# SCRAPER21 — fallback
# ─────────────────────────────────────

async def scrape_scraper21(username: str) -> str:
    if not is_service_active("scraper21"):
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
                mark_service_exhausted("scraper21")
                return ""
            posts = data.get("data", {}).get("posts", [])
            text  = " ".join([
                p.get("caption", "") or ""
                for p in posts[:5]
            ])
            print(f"[Scraper21] ✅ @{username}")
            return text
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
    except Exception as e:
        print(f"[URLMeta] Erreur : {e}")
        return {"valid": False, "type": "error"}


# ─────────────────────────────────────
# ENRICHISSEMENT D'UN PROFIL
# ─────────────────────────────────────

async def enrich_profile(profile: dict) -> dict:
    username = profile["username"]

    try:
        # ÉTAPE 1 — Infos profil via Looter
        data = await get_profile_looter(username)

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

        # ÉTAPE 2 — Scraping signaux
        scraped_text = await scrape_playwright(username)

        # ÉTAPE 3 — Vérification site
        site_info = await check_website(ext_link) if ext_link else {
            "valid": False, "type": "none"
        }

        # Texte complet
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
            r"(?:\+33|0033|0[1-7])[\s.\-]?\d{2}[\s.\-]?\d{2}[\s.\-]?\d{2}[\s.\-]?\d{2}",
            full_text
        )

        # ── Détection France avancée ──
        is_french = detect_france(full_text)

        # Validation
        followers_valid = MIN_FOLLOWERS <= followers <= MAX_FOLLOWERS

        # Rejet immédiat si hors France détecté
        if not is_french and followers_valid:
            # On garde quand même mais on marque
            pass

        is_active = (
            posts_count > 0 or
            is_professional or
            is_business or
            len(bio) > 20
        )

        await asyncio.sleep(random.uniform(2.0, 4.0))

        print(
            f"[Enricher] @{username} → "
            f"{followers} followers | "
            f"FR:{is_french} | "
            f"DM:{sells_via_dm} | "
            f"WA:{has_whatsapp} | "
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
