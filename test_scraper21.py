import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

KEY = os.getenv("RAPIDAPI_KEY")
HOST = "instagram-scraper21.p.rapidapi.com"
BASE = f"https://{HOST}"

HEADERS = {
    "x-rapidapi-host": HOST,
    "x-rapidapi-key":  KEY
}

ENDPOINTS = [
    "/api/v1/search?query=coiffeur",
    "/api/v1/hashtag?name=coiffeur",
    "/api/v1/hashtag/posts?name=coiffeur",
    "/api/v1/tag?name=coiffeur",
    "/api/v1/explore/hashtag?tag=coiffeur",
    "/api/v1/feed/hashtag?hashtag=coiffeur",
]

async def test():
    async with httpx.AsyncClient(timeout=15) as client:
        for endpoint in ENDPOINTS:
            try:
                r = await client.get(
                    f"{BASE}{endpoint}",
                    headers=HEADERS
                )
                print(f"{r.status_code} → {endpoint} : {r.text[:100]}")
            except Exception as e:
                print(f"ERR → {endpoint} : {e}")
            await asyncio.sleep(1)

asyncio.run(test())
