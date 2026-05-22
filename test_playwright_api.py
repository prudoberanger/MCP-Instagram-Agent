import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

KEY  = os.getenv("RAPIDAPI_KEY")
HOST = "playwright-dynamic-scraper.p.rapidapi.com"
BASE = f"https://{HOST}"

HEADERS = {
    "x-rapidapi-host": HOST,
    "x-rapidapi-key":  KEY,
    "Content-Type":    "application/json"
}

URL = "https://www.instagram.com/barberhome.france/"

async def test():
    async with httpx.AsyncClient(timeout=30) as client:

        # Test 1 — Extraction texte
        try:
            r = await client.get(
                f"{BASE}/api/scrape/text",
                headers=HEADERS,
                params={"url": URL}
            )
            print(f"✅ TEXT → {r.status_code}")
            print(f"   {r.text[:300]}")
        except Exception as e:
            print(f"❌ TEXT → {e}")

        await asyncio.sleep(2)

        # Test 2 — Extraction HTML
        try:
            r = await client.get(
                f"{BASE}/api/scrape/html",
                headers=HEADERS,
                params={"url": URL}
            )
            print(f"✅ HTML → {r.status_code}")
            print(f"   {r.text[:300]}")
        except Exception as e:
            print(f"❌ HTML → {e}")

        await asyncio.sleep(2)

        # Test 3 — Métadonnées
        try:
            r = await client.get(
                f"{BASE}/api/scrape/metadata",
                headers=HEADERS,
                params={"url": URL}
            )
            print(f"✅ METADATA → {r.status_code}")
            print(f"   {r.text[:300]}")
        except Exception as e:
            print(f"❌ METADATA → {e}")

asyncio.run(test())
