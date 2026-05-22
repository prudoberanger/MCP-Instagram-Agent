import asyncio
import httpx
from config.settings import OPENROUTER_API_KEY, QWEN_MODEL

async def test():
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
               "model": "google/gemma-3-27b-it:free",
                "messages": [
                    {"role": "user", "content": "Réponds juste: VALIDE"}
                ],
                "max_tokens": 50
            }
        )
        import json
        print(json.dumps(r.json(), indent=2))

asyncio.run(test())
