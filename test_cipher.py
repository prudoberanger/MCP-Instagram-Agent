import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

KEY  = os.getenv("RAPIDAPI_KEY")
HOST = "instagram-api-profiles-posts-reels-stories-hashtags.p.rapidapi.com"
BASE = f"https://{HOST}"

HEADERS = {
    "x-rapidapi-host": HOST,
    "x-rapidapi-key":  KEY
}

ENDPOINTS = [
    "/api/search?q=coiffeur&type=users",
    "/api/search?query=coiffeur",
    "/api/user?username=nike",
    "/api/profile?username=nike",
    "/api/posts?username=nike",
    "/api/tag?name=coiffeur",
    "/api/tags/coiffeur",
    "/api/explore",
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
                print(f"   {r.text[:150]}")
            except Exception as e:
                print(f"ERR → {endpoint} : {e}")
            await asyncio.sleep(1)

asyncio.run(test())
