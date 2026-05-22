import asyncio
import httpx
from config.settings import OPENROUTER_API_KEY

async def test():
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            "https://openrouter.ai/api/v1/models",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}"
            }
        )
        data = r.json()
        models = data.get("data", [])

        # Filtre modèles gratuits
        free = [
            m["id"] for m in models
            if ":free" in m["id"]
        ]

        for m in free:
            print(m)

asyncio.run(test())
