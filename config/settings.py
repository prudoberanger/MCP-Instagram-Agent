# config/settings.py

from dotenv import load_dotenv
import os

load_dotenv()

# ─────────────────────────────────────
# RAPIDAPI — une seule clé active
# ─────────────────────────────────────
RAPIDAPI_KEY    = os.getenv("RAPIDAPI_KEY")

# ─────────────────────────────────────
# HOSTS RAPIDAPI
# ─────────────────────────────────────
LOOTER_HOST     = os.getenv("LOOTER_HOST",     "instagram-looter2.p.rapidapi.com")
CHEAPEST_HOST   = os.getenv("CHEAPEST_HOST",   "instagram-cheapest.p.rapidapi.com")
PLAYWRIGHT_HOST = os.getenv("PLAYWRIGHT_HOST", "playwright-dynamic-scraper.p.rapidapi.com")
SCRAPER21_HOST  = os.getenv("SCRAPER21_HOST",  "instagram-scraper21.p.rapidapi.com")
URLMETA_HOST    = os.getenv("URLMETA_HOST",    "url-metadata-api1.p.rapidapi.com")

# ─────────────────────────────────────
# AUTRES API
# ─────────────────────────────────────
OPENROUTER_API_KEY   = os.getenv("OPENROUTER_API_KEY")
SUPABASE_URL         = os.getenv("SUPABASE_URL")
SUPABASE_KEY         = os.getenv("SUPABASE_KEY")
GOOGLE_CSE_API_KEY   = os.getenv("GOOGLE_CSE_API_KEY")
GOOGLE_CSE_CX        = os.getenv("GOOGLE_CSE_CX")
INSTAGRAM_USERNAME   = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD   = os.getenv("INSTAGRAM_PASSWORD")
INSTAGRAM_SESSION_ID = os.getenv("INSTAGRAM_SESSION_ID")

# ─────────────────────────────────────
# MODÈLES IA
# ─────────────────────────────────────
QWEN_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
GLM_MODEL  = "z-ai/glm-4.5-air:free"

# ─────────────────────────────────────
# LIMITES
# ─────────────────────────────────────
MAX_FETCH_PER_SOURCE = 40
MIN_VALID_FINAL      = 5
MAX_VALID_FINAL      = 15
MAX_FETCH_TOTAL      = 90
MIN_FOLLOWERS        = 500
MAX_FOLLOWERS        = 10_000
WINDOW_HOURS         = 4

# ─────────────────────────────────────
# NICHES + HASHTAGS
# ─────────────────────────────────────
NICHES = {
    "ecommerce": {
        "label": "E-commerce & Boutiques en ligne",
        "hashtags": [
            "boutiqueenligne",
            "shopenligne",
            "ventedirect",
            "modeenligne",
            "accessoiresfemme"
        ],
    },
    "beaute": {
        "label": "Services Beauté & Esthétique",
        "hashtags": [
            "estheticienne",
            "institutbeaute",
            "onglerie",
            "manchurage",
            "soinsbeaute"
        ],
    },
    "coiffure": {
        "label": "Coiffure & Barber Shop",
        "hashtags": [
            "coiffeurafro",
            "barbershop",
            "coiffuremaison",
            "tresseafricaine",
            "coiffurebobo"
        ],
    },
    "photo": {
        "label": "Photographie & Création de contenu",
        "hashtags": [
            "photographe",
            "shootingphoto",
            "portraitphoto",
            "photographieprofessionnelle",
            "reportagephoto"
        ],
    },
    "sport": {
        "label": "Coaching Sportif & Fitness",
        "hashtags": [
            "coachsportif",
            "coachfitness",
            "musculationmaison",
            "poidsetmuscles",
            "coachperso"
        ],
    },
    "coaching": {
        "label": "Coaching Business & Formation",
        "hashtags": [
            "coachbusiness",
            "entrepreneuriat",
            "formationenligne",
            "mentorat",
            "developpementpersonnel"
        ],
    },
    "restauration": {
        "label": "Restauration & Food Business",
        "hashtags": [
            "chefcuisinier",
            "traiteur",
            "cuisinemaison",
            "repaslivraison",
            "cuisineduchef"
        ],
    },
    "patisserie": {
        "label": "Pâtisserie & Traiteurs",
        "hashtags": [
            "patisseriemaison",
            "gateausurcommande",
            "cakedesign",
            "patissierartisan",
            "chouquettes"
        ],
    },
    "immobilier": {
        "label": "Immobilier & Agences",
        "hashtags": [
            "agentimmobilier",
            "investissementimmobilier",
            "achatappartement",
            "locationappartement",
            "immobilierneuf"
        ],
    },
    "creatifs": {
        "label": "Freelances Créatifs",
        "hashtags": [
            "graphiste",
            "videoaste",
            "montagevideos",
            "designgraphique",
            "creationcontenu"
        ],
    }
}

# ─────────────────────────────────────
# SIGNAUX COMMERCIAUX
# ─────────────────────────────────────
SIGNALS_DM = [
    "dm pour commander", "dm pour infos",
    "envoyez un message", "contactez-nous en dm",
    "écrivez-nous", "message privé",
    "commande par dm", "dm pour tarif"
]

SIGNALS_WHATSAPP = [
    "wa.me", "whatsapp", "whats app",
    "contactez sur whatsapp",
    "commandez sur whatsapp",
    "wa.me/", "+33"
]

SIGNALS_WEAK_LINK = [
    "linktr.ee", "beacons.ai",
    "linkin.bio", "bio.link", "taplink"
]

SIGNALS_CUSTOMER = [
    "c'est combien", "vous livrez",
    "disponible", "je veux commander",
    "comment commander", "prix svp",
    "c'est dispo", "vous expédiez"
]

SIGNALS_EXCLUDE = [
    "étudiant", "en formation",
    "débutant", "portfolio",
    "je cherche un emploi",
    "disponible pour missions",
    "open to work"
]
