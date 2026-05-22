import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

KEY = os.getenv("RAPIDAPI_KEY")

async def test():
    async with httpx.AsyncClient(timeout=15) as client:

        # API 1 — instagram-scraper21
        try:
            r = await client.get(
                "https://instagram-scraper21.p.rapidapi.com/api/v1/ping",
                headers={
                    "x-rapidapi-host": "instagram-scraper21.p.rapidapi.com",
                    "x-rapidapi-key":  KEY
                }
            )
            print(f"✅ API1 scraper21 → {r.status_code} : {r.text[:100]}")
        except Exception as e:
            print(f"❌ API1 scraper21 → {e}")

        await asyncio.sleep(1)

        # API 2 — scraper-reels-posts-profiles1
        try:
            r = await client.get(
                "https://instagram-scraper-reels-posts-profiles1.p.rapidapi.com/search",
                headers={
                    "x-rapidapi-host": "instagram-scraper-reels-posts-profiles1.p.rapidapi.com",
                    "x-rapidapi-key":  KEY
                },
                params={"query": "coiffeur"}
            )
            print(f"✅ API2 reels-posts → {r.status_code} : {r.text[:100]}")
        except Exception as e:
            print(f"❌ API2 reels-posts → {e}")

        await asyncio.sleep(1)

        # API 3 — scraper-stable-api
        try:
            r = await client.get(
                "https://instagram-scraper-stable-api.p.rapidapi.com/get_ig_user_followers_v2.php",
                headers={
                    "x-rapidapi-host": "instagram-scraper-stable-api.p.rapidapi.com",
                    "x-rapidapi-key":  KEY
                },
                params={"username": "coiffeur_france"}
            )
            print(f"✅ API3 stable → {r.status_code} : {r.text[:100]}")
        except Exception as e:
            print(f"❌ API3 stable → {e}")

asyncio.run(test())
