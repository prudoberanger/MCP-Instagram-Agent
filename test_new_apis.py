import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

KEY = os.getenv("RAPIDAPI_KEY")

async def test():
    async with httpx.AsyncClient(timeout=15) as client:

        # API 1 — Cipher (collecte hashtag)
        try:
            r = await client.get(
                "https://instagram-api-profiles-posts-reels-stories-hashtags.p.rapidapi.com/api/search",
                headers={
                    "x-rapidapi-host": "instagram-api-profiles-posts-reels-stories-hashtags.p.rapidapi.com",
                    "x-rapidapi-key":  KEY,
                    "Content-Type":    "application/json"
                },
                params={"query": "coiffeurfrance", "type": "hashtag"}
            )
            print(f"✅ Cipher → {r.status_code}")
            print(f"   {r.text[:300]}")
        except Exception as e:
            print(f"❌ Cipher → {e}")

        await asyncio.sleep(2)

        # API 2 — Cheapest (enrichissement profil)
        try:
            r = await client.get(
                "https://instagram-cheapest.p.rapidapi.com/api/v1/instagram/user/coiffeur_france",
                headers={
                    "x-rapidapi-host": "instagram-cheapest.p.rapidapi.com",
                    "x-rapidapi-key":  KEY,
                    "Content-Type":    "application/json"
                }
            )
            print(f"✅ Cheapest → {r.status_code}")
            print(f"   {r.text[:300]}")
        except Exception as e:
            print(f"❌ Cheapest → {e}")

asyncio.run(test())
