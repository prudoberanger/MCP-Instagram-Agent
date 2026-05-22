# tools/scorer_glm.py

import httpx
import json
from config.settings import OPENROUTER_API_KEY, GLM_MODEL


# ─────────────────────────────────────
# PROMPT GLM
# ─────────────────────────────────────

def build_scoring_prompt(profile: dict) -> str:
    return f"""Tu es un consultant expert en optimisation des ventes pour PME françaises.

Analyse ce business Instagram et attribue un score sur 100.

CRITÈRES DE SCORING :

1. ACTIVITÉ (25pts)
   - Publications régulières
   - Engagement visible
   - Réponses aux commentaires

2. CLARTÉ DE L'OFFRE (25pts)
   - Produits/services clairement présentés
   - Prix visibles ou mentionnés
   - Appel à l'action présent

3. NIVEAU DE DOULEUR (30pts) ← PRIORITÉ MAXIMALE
   - Vend uniquement via DM/WhatsApp = score élevé
   - Pas de site web réel = score élevé
   - Utilise Linktree/Beacons = score moyen
   - A déjà un vrai site = score bas
   - Perd des clients à cause d'un système désorganisé

4. ANCRAGE FRANCE (20pts)
   - Bio en français
   - Clientèle française visible
   - Hashtags français
   - Localisation France mentionnée

PROFIL À SCORER :
- Username        : @{profile.get('username')}
- Bio             : {profile.get('bio', 'Aucune')}
- Followers       : {profile.get('followers', 0)}
- Dernier post    : il y a {profile.get('last_post_days', 999)} jours
- Vend via DM     : {profile.get('sells_via_dm', False)}
- WhatsApp        : {profile.get('has_whatsapp', False)}
- Linktree        : {profile.get('has_linktree', False)}
- Beacons         : {profile.get('has_beacons', False)}
- Vrai site web   : {profile.get('has_real_website', False)}
- Lien externe    : {profile.get('external_link', 'Aucun')}
- Commentaires clients : {profile.get('has_customer_comments', False)}
- Niche           : {profile.get('niche', 'Inconnue')}
- Validé par Qwen : {profile.get('qwen_reason', '')}

RÉPONDS UNIQUEMENT avec ce JSON exact, rien d'autre :
{{
  "score_total": 0,
  "score_activite": 0,
  "score_offre": 0,
  "score_douleur": 0,
  "score_france": 0,
  "raison": "phrase courte expliquant le score global"
}}
"""


# ─────────────────────────────────────
# APPEL GLM VIA OPENROUTER
# ─────────────────────────────────────

async def score_with_glm(profile: dict) -> dict:
    """
    Envoie le profil à GLM-4.5 via OpenRouter
    Retourne le profil avec le score complet
    """
    prompt = build_scoring_prompt(profile)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": GLM_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 200,
                    "temperature": 0.1
                }
            )

            data = response.json()
            raw = data["choices"][0]["message"]["content"].strip()

            # Nettoie le JSON si besoin
            raw = raw.replace("```json", "").replace("```", "").strip()
            scores = json.loads(raw)

            print(
                f"[GLM] @{profile['username']} → "
                f"Score {scores['score_total']}/100 — {scores['raison']}"
            )

            return {
                **profile,
                "score_total":    scores.get("score_total", 0),
                "score_activite": scores.get("score_activite", 0),
                "score_offre":    scores.get("score_offre", 0),
                "score_douleur":  scores.get("score_douleur", 0),
                "score_france":   scores.get("score_france", 0),
                "glm_reason":     scores.get("raison", "")
            }

    except Exception as e:
        print(f"[GLM] Erreur @{profile['username']} : {e}")
        return {
            **profile,
            "score_total":    0,
            "score_activite": 0,
            "score_offre":    0,
            "score_douleur":  0,
            "score_france":   0,
            "glm_reason":     f"Erreur scoring : {e}"
        }


# ─────────────────────────────────────
# SCORING BATCH — tous les profils
# ─────────────────────────────────────

async def score_all_profiles(profiles: list[dict]) -> list[dict]:
    """
    Score tous les profils validés par Qwen
    Séquentiel pour éviter le rate limit
    """
    import asyncio
    scored = []

    for i, profile in enumerate(profiles):
        print(f"[GLM] Score {i+1}/{len(profiles)} → @{profile['username']}")

        result = await score_with_glm(profile)
        scored.append(result)

        # Pause entre chaque appel API
        await asyncio.sleep(1.5)

    # Tri par score décroissant
    scored.sort(key=lambda x: x["score_total"], reverse=True)

    print(f"[GLM] Scoring terminé — meilleur score : {scored[0]['score_total']}/100")
    return scored
