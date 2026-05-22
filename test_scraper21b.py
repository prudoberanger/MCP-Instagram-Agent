import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

KEY  = os.getenv("RAPIDAPI_KEY")
HOST = "instagram-scraper21.p.rapidapi.com"
BASE = f"https://{HOST}"

HEADERS = {
    "x-rapidapi-host": HOST,
    "x-rapidapi-key":  KEY
}

ENDPOINTS = [
    "/api/v1/profile?username=nike",
    "/api/v1/user?username=nike",
    "/api/v1/user/posts?username=nike",
    "/api/v1/user/info?username=nike",
    "/api/v1/posts?username=nike",
    "/api/v1/hashtag/search?q=coiffeur",
    "/api/v1/tags?q=coiffeur",
]

async def test():
    async with httpx.AsyncClient(timeout=15) as client:
        for endpoint in ENDPOINTS:
            try:
                r = await client.get(
                    f"{BASE}{endpoint}",
                    headers=HEADERS
                )
                print(f"{r.status_code} → {endpoint}")
                print(f"  {r.text[:150]}")
            except Exception as e:
                print(f"ERR → {endpoint} : {e}")
            await asyncio.sleep(1)

asyncio.run(test())
