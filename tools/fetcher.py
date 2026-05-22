# tools/fetcher.py

import asyncio
import random
import httpx
from config.settings import (
    NICHES,
    MAX_FETCH_PER_SOURCE,
    LOOTER_HOST,
    RAPIDAPI_KEY,
    GOOGLE_CSE_API_KEY,
    GOOGLE_CSE_CX
)
from tools.webhook_quota import (
    is_quota_exceeded,
    is_service_active,
    mark_service_exhausted
)

TIMEOUT = httpx.Timeout(15.0, connect=5.0)

RAPIDAPI_HEADERS = {
    "x-rapidapi-host": LOOTER_HOST,
    "x-rapidapi-key":  RAPIDAPI_KEY
}


# ─────────────────────────────────────
# LOOTER
# ─────────────────────────────────────

async def fetch_looter_with_hashtag(hashtag: str) -> list[dict]:
    profiles = []

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            r    = await client.get(
                f"https://{LOOTER_HOST}/search",
                headers=RAPIDAPI_HEADERS,
                params={"query": hashtag}
            )
            data = r.json()
            text = str(data)

            if is_quota_exceeded(text):
                print(f"[Looter] Quota épuisé → change RAPIDAPI_KEY dans .env")
                mark_service_exhausted("looter")
                return "QUOTA_EXCEEDED"

            for item in data.get("users", []):
                user     = item.get("user", {})
                username = user.get("username", "")
                if username:
                    profiles.append({
                        "username":  username,
                        "followers": 0,
                        "source":    "looter"
                    })

            for media in data.get("medias", []):
                owner    = media.get("owner") or {}
                username = owner.get("username", "")
                if username and username not in [
                    p["username"] for p in profiles
                ]:
                    profiles.append({
                        "username":  username,
                        "followers": 0,
                        "source":    "looter"
                    })

        except httpx.ConnectTimeout:
            print(f"[Looter] Timeout réseau #{hashtag} — pas épuisé")
        except Exception as e:
            print(f"[Looter] Erreur #{hashtag} : {e}")

    return profiles


async def fetch_looter(niche: str) -> list[dict]:
    if not is_service_active("looter"):
        print("[Looter] ⚠️ Service désactivé → Google CSE")
        return []

    all_profiles = []
    hashtags     = NICHES[niche]["hashtags"].copy()
    random.shuffle(hashtags)

    for hashtag in hashtags:
        if len(all_profiles) >= MAX_FETCH_PER_SOURCE:
            break

        print(f"[Looter] Hashtag #{hashtag}")
        result = await fetch_looter_with_hashtag(hashtag)

        if result == "QUOTA_EXCEEDED":
            break

        if isinstance(result, list):
            print(f"[Looter] ✅ {len(result)} profils")
            for p in result:
                if p["username"] not in [
                    x["username"] for x in all_profiles
                ]:
                    all_profiles.append(p)

        await asyncio.sleep(random.uniform(1.5, 3.0))

    print(f"[Looter] Total : {len(all_profiles)} profils")
    return all_profiles[:MAX_FETCH_PER_SOURCE]


# ─────────────────────────────────────
# GOOGLE CSE — fallback
# ─────────────────────────────────────

async def fetch_google_cse(niche: str) -> list[dict]:
    profiles = []
    keywords = NICHES[niche]["google_keywords"]

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for keyword in keywords:
            if len(profiles) >= MAX_FETCH_PER_SOURCE:
                break
            try:
                r = await client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params={
                        "key": GOOGLE_CSE_API_KEY,
                        "cx":  GOOGLE_CSE_CX,
                        "q":   f"site:instagram.com {keyword}",
                        "num": 10
                    }
                )
                data = r.json()

                if "error" in data:
                    print(f"[Google] Erreur : {data['error'].get('message')}")
                    break

                for item in data.get("items", []):
                    if len(profiles) >= MAX_FETCH_PER_SOURCE:
                        break
                    link = item.get("link", "")
                    if "instagram.com/" in link:
                        parts    = link.split("instagram.com/")
                        username = parts[1].strip("/").split("/")[0] \
                            if len(parts) > 1 else ""
                        if username and username not in [
                            "p", "explore", "reel", "stories"
                        ] and username not in [
                            p["username"] for p in profiles
                        ]:
                            profiles.append({
                                "username":  username,
                                "followers": 0,
                                "source":    "google"
                            })

                await asyncio.sleep(random.uniform(1.0, 2.0))

            except Exception as e:
                print(f"[Google] Erreur '{keyword}' : {e}")
                continue

    print(f"[Google CSE] {len(profiles)} profils")
    return profiles


# ─────────────────────────────────────
# MERGE & DEDUPE
# ─────────────────────────────────────

def merge_and_dedupe(
    looter: list[dict],
    google: list[dict]
) -> list[dict]:
    seen   = set()
    merged = []

    for p in looter + google:
        username = p.get("username", "")
        if username and username not in seen:
            seen.add(username)
            merged.append(p)

    merged = merged[:90]
    print(f"[Merge] {len(merged)} profils uniques")
    return merged


# ─────────────────────────────────────
# ORCHESTRATEUR
# ─────────────────────────────────────

async def fetch_all_sources(niche: str) -> list[dict]:
    print(f"\n[Fetch] Démarrage → niche : {niche}")

    # PRIORITÉ 1 — Looter
    looter_profiles = await fetch_looter(niche)
    print(f"[Looter] → {len(looter_profiles)} profils")

    # PRIORITÉ 2 — Google CSE si Looter insuffisant
    google_profiles = []
    if len(looter_profiles) < 5 or not is_service_active("looter"):
        print("[Fetch] Looter insuffisant → Google CSE fallback")
        google_profiles = await fetch_google_cse(niche)
        print(f"[Google] → {len(google_profiles)} profils")
    else:
        print("[Google] → skipped (Looter suffisant)")

    merged = merge_and_dedupe(looter_profiles, google_profiles)
    print(f"[Fetch] ✅ {len(merged)} profils prêts")
    return merged
