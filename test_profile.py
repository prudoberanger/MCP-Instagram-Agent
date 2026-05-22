import asyncio
import httpx
from config.settings import RAPIDAPI_KEY, RAPIDAPI_HOST

HEADERS = {
    "x-rapidapi-host": RAPIDAPI_HOST,
    "x-rapidapi-key":  RAPIDAPI_KEY
}

async def test():
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"https://{RAPIDAPI_HOST}/profile",
            headers=HEADERS,
            params={"username": "barberhome.france"}
        )
        import json
        data = r.json()
        print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])

asyncio.run(test())
