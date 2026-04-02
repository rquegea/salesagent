"""
Configuración global del T&T Outreach Agent
"""

# ══════════════════════════════════════════════════════════════
# ICP FILTERS (Apollo People API Search)
# ══════════════════════════════════════════════════════════════

ICP_SHIELDAI = {
    "person_titles": [
        # English titles
        "CISO", "Chief Information Security Officer",
        "CTO", "Chief Technology Officer",
        "CIO", "Chief Information Officer",
        "DPO", "Data Protection Officer",
        "VP Security", "VP IT", "VP Engineering",
        "Head of IT", "Head of Security",
        "Director of Information Security",
        "IT Security Manager", "Information Security Manager",
        "Cybersecurity Manager", "IT Manager",
        "Tech Lead",
        # Spanish titles (España)
        "Director de Seguridad", "Director de Seguridad Informática",
        "Director de TI", "Director de Informática", "Director de Tecnología",
        "Director de Sistemas", "Director Técnico",
        "Responsable de Ciberseguridad", "Responsable de Seguridad",
        "Responsable de IT", "Responsable de Sistemas",
        "Responsable de Protección de Datos",
        "Director de Protección de Datos", "DPD",
        "Gerente de Sistemas", "Jefe de IT"
    ],
    "employee_ranges": ["25-50", "51-200", "201-500"],
    "person_locations": ["Spain"],  # ONLY Spain, not other countries
    "q_keywords": "",
}

ICP_TWOLAPS = {
    "person_titles": [
        "CMO", "Chief Marketing Officer",
        "Head of Marketing", "Head of Digital",
        "VP Marketing", "Director de Marketing",
        "SEO Manager", "Head of SEO",
        "Digital Marketing Manager"
    ],
    "employee_ranges": ["25-50", "51-200", "201-500"],
    "person_locations": ["Spain", "Mexico", "Colombia", "Argentina", "Chile"],
    "keyword_tags": ["education", "fmcg", "retail", "food"],
}

# ══════════════════════════════════════════════════════════════
# CADENCIAS
# ══════════════════════════════════════════════════════════════

CADENCE = {
    "cold_email": 0,
    "linkedin_connect": 3,
    "follow_up_1": 7,
    "follow_up_2": 14,
    "max_touchpoints": 4,
    "min_days_between": 3,
}

# ══════════════════════════════════════════════════════════════
# LÍMITES DIARIOS
# ══════════════════════════════════════════════════════════════

DAILY_LIMITS = {
    "new_prospects": 50,
    "claude_calls": 30,
    "emails_sent": 50,
    "linkedin_requests": 20,
}

# ══════════════════════════════════════════════════════════════
# DESCRIPCIONES DE PRODUCTOS
# ══════════════════════════════════════════════════════════════

PRODUCT_DESCRIPTIONS = {
    "shieldai": (
        "ShieldAI es una extensión de Chrome que detecta y bloquea datos sensibles "
        "(DNIs, tarjetas de crédito, datos médicos, contraseñas) antes de que se envíen "
        "a ChatGPT, Gemini, Copilot o cualquier IA. Protege a la empresa de fugas de datos "
        "involuntarias sin bloquear el uso de IA."
    ),
    "twolaps": (
        "2laps es una plataforma de monitorización de visibilidad en IA (GEO). "
        "Mide cómo aparece tu marca cuando la gente pregunta a ChatGPT, Gemini, Perplexity "
        "o cualquier IA generativa. Detecta quién te está ganando en las respuestas de IA "
        "y te dice cómo corregirlo."
    ),
}

# API Base URLs
APOLLO_API_BASE = "https://api.apollo.io/api/v1"
ANTHROPIC_API_BASE = "https://api.anthropic.com/v1"

# Estado mappings
PROSPECT_STATUSES = [
    "new",
    "drafted",
    "sent",
    "followed_up_1",
    "followed_up_2",
    "replied",
    "meeting",
    "closed",
    "exhausted",
]
