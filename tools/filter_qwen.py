# tools/filter_qwen.py

import httpx
from config.settings import OPENROUTER_API_KEY, QWEN_MODEL, SIGNALS_EXCLUDE


# ─────────────────────────────────────
# PROMPT QWEN
# ─────────────────────────────────────

def build_prompt(profile: dict) -> str:
    return f"""Tu es un expert en prospection commerciale Instagram France.

Analyse ce profil et réponds VALIDE ou INVALIDE.

VALIDE si AU MOINS UN de ces critères est vrai :
- Propose un service ou produit (coiffure, sport, beauté, food, coaching...)
- A une bio qui mentionne une activité professionnelle
- Est un compte professionnel ou business
- A plus de 500 followers et semble actif

INVALIDE uniquement si :
- Compte complètement vide ou spam évident
- Bot ou faux compte

Sois LARGE dans ta validation. En cas de doute → VALIDE.

PROFIL :
- Username : @{profile.get('username')}
- Bio : {profile.get('bio', 'Aucune')}
- Followers : {profile.get('followers', 0)}
- Professionnel : {profile.get('is_professional', False)}
- Business : {profile.get('is_business', False)}
- Lien externe : {profile.get('external_link', 'Aucun')}

Réponds UNIQUEMENT : VALIDE ou INVALIDE
Puis une courte phrase expliquant pourquoi.
"""


# ─────────────────────────────────────
# APPEL QWEN VIA OPENROUTER
# ─────────────────────────────────────

async def filter_with_qwen(profile: dict) -> dict:
    """
    Envoie le profil à Qwen via OpenRouter
    Retourne le profil enrichi avec le résultat du filtre
    """
    prompt = build_prompt(profile)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": QWEN_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 100,
                    "temperature": 0.1   # réponse stable et précise
                }
            )

            data = response.json()
            raw = data["choices"][0]["message"]["content"].strip()

            # Parse la réponse
            lines = raw.split("\n")
            verdict = lines[0].strip().upper()
            reason  = lines[1].strip() if len(lines) > 1 else ""

            qwen_valid = verdict == "VALIDE"

            print(
                f"[Qwen] @{profile['username']} → "
                f"{'✅ VALIDE' if qwen_valid else '❌ INVALIDE'} — {reason}"
            )

            return {
                **profile,
                "qwen_valid":      qwen_valid,
                "qwen_confidence": 1.0 if qwen_valid else 0.0,
                "qwen_reason":     reason
            }

    except Exception as e:
        print(f"[Qwen] Erreur @{profile['username']} : {e}")
        return {
            **profile,
            "qwen_valid":      False,
            "qwen_confidence": 0.0,
            "qwen_reason":     f"Erreur : {e}"
        }


# ─────────────────────────────────────
# FILTRE BATCH — tous les profils
# ─────────────────────────────────────

async def filter_all_profiles(profiles: list[dict]) -> list[dict]:
    """
    Filtre tous les profils avec Qwen
    Séquentiel — un par un pour éviter le rate limit
    """
    import asyncio
    valid = []

    for i, profile in enumerate(profiles):
        print(f"[Qwen] Analyse {i+1}/{len(profiles)} → @{profile['username']}")

        result = await filter_with_qwen(profile)

        if result["qwen_valid"]:
            valid.append(result)

        # Pause entre chaque appel API
        await asyncio.sleep(1.5)

    print(f"[Qwen] {len(valid)}/{len(profiles)} profils validés")
    return valid
