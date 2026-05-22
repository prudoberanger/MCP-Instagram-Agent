# test_looter.py

import asyncio
import httpx
from config.settings import RAPIDAPI_KEY, RAPIDAPI_HOST

async def test():
    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key":  RAPIDAPI_KEY
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(
            f"https://{RAPIDAPI_HOST}/hashtag",
            headers=headers,
            params={"query": "coiffeurfrance"}
        )
        print("Status :", response.status_code)
        print("Réponse :", response.text[:500])

asyncio.run(test())
