# test_endpoints.py

import asyncio
import httpx
from config.settings import RAPIDAPI_KEY, RAPIDAPI_HOST

# Endpoints possibles sur instagram-looter2
ENDPOINTS_TO_TEST = [
    "/search",
    "/tag",
    "/tags",
    "/hashtag",
    "/hashtags",
    "/feed/tag",
    "/feed/hashtag",
    "/media/tag",
    "/posts/tag",
    "/explore/tags",
]

async def test():
    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key":  RAPIDAPI_KEY
    }

    async with httpx.AsyncClient(timeout=30) as client:
        for endpoint in ENDPOINTS_TO_TEST:
            try:
                response = await client.get(
                    f"https://{RAPIDAPI_HOST}{endpoint}",
                    headers=headers,
                    params={"query": "coiffeurfrance", "tag": "coiffeurfrance"}
                )
                print(f"{endpoint} → {response.status_code} : {response.text[:100]}")
            except Exception as e:
                print(f"{endpoint} → Erreur : {e}")
            
            await asyncio.sleep(1)

asyncio.run(test())
