import asyncio
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

KEY  = os.getenv("RAPIDAPI_KEY")
HOST = "instagram-cheapest.p.rapidapi.com"

async def test():
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"https://{HOST}/api/v1/instagram/user/barberhome.france",
            headers={
                "x-rapidapi-host": HOST,
                "x-rapidapi-key":  KEY
            }
        )
        data = r.json()
        print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])

asyncio.run(test())
