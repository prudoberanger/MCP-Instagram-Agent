import asyncio
import httpx
from config.settings import OPENROUTER_API_KEY

MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "google/gemma-3-12b-it:free",
    "google/gemma-3-4b-it:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "z-ai/glm-4.5-air:free",
    "openai/gpt-oss-20b:free",
]

async def test():
    async with httpx.AsyncClient(timeout=30) as client:
        for model in MODELS:
            try:
                r = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "user", "content": "Say: OK"}
                        ],
                        "max_tokens": 10
                    }
                )
                data = r.json()
                if "choices" in data:
                    print(f"✅ {model} → FONCTIONNE")
                else:
                    code = data.get("error", {}).get("code", "?")
                    print(f"❌ {model} → {code}")
            except Exception as e:
                print(f"⚠️  {model} → {e}")
            await asyncio.sleep(2)

asyncio.run(test())
