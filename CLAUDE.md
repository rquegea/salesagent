# T&T Outreach Agent — CLAUDE.md

## Qué es esto

Sistema automatizado de prospección y outreach B2B para Truco y Trufa. Contacta automáticamente 25-50 empresas/día para dos productos: **ShieldAI** (extensión Chrome DLP) y **2laps** (GEO/AI visibility monitoring). Corre en local o VPS. Sin interfaz web. Solo scripts + cron + base de datos.

---

## Stack

| Componente | Herramienta | Coste |
|---|---|---|
| Base de datos de contactos | Apollo.io API (plan Professional) | $79/mes |
| Base de datos interna | Neon Postgres (free tier) | $0 |
| Personalización de mensajes | Claude API (Sonnet) | ~$5-10/mes |
| Envío email + LinkedIn | Unipile API | €49/mes |
| Lenguaje | Python 3.11+ | — |
| Ejecución | Local (macOS cron) o VPS (Hetzner €4/mes) | $0-4/mes |
| **TOTAL** | | **~€135/mes** |

---

## Arquitectura

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   Apollo    │────▶│  Prospector  │────▶│  Composer   │────▶│    Sender    │
│ (prospects) │     │  (generar    │     │  (generar   │     │  (enviar     │
│             │     │  + dedup)    │     │  mensajes)  │     │  email/LI)   │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
       │                    │                    │                     │
       └────────────────────┴────────────────────┴─────────────────────┘
                              DB (Neon Postgres)
                                    │
                                    ▼
                              Follower
                         (check replies + FU)
```

---

## Estructura de archivos

```
tt-outreach-agent/
├── CLAUDE.md              ← Este archivo
├── .env                   ← API keys (NO commitear)
├── requirements.txt       ← Dependencias Python
├── main.py                ← Orquestador principal (cron entry point)
├── config.py              ← ICP, cadencias, límites
├── prospector.py          ← Busca nuevos prospects en Apollo
├── composer.py            ← Genera drafts via Claude API
├── sender.py              ← Envía emails + LinkedIn requests
├── follower.py            ← Lee respuestas + genera follow-ups
├── db.py                  ← Conexión y queries a DB
├── templates/
│   ├── shieldai_cold.txt  ← Prompt template para ShieldAI primer contacto
│   ├── shieldai_fu1.txt   ← Prompt template para ShieldAI follow-up 1
│   ├── shieldai_fu2.txt   ← Prompt template para ShieldAI follow-up 2
│   ├── twolaps_cold.txt   ← Prompt template para 2laps primer contacto
│   ├── twolaps_fu1.txt    ← Prompt template para 2laps follow-up 1
│   └── twolaps_fu2.txt    ← Prompt template para 2laps follow-up 2
└── logs/
    └── outreach.log       ← Log de actividad
```

---

## Base de datos — Schema Neon

```sql
CREATE TABLE prospects (
    id              SERIAL PRIMARY KEY,
    -- Datos del contacto
    apollo_id       TEXT UNIQUE,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    email           TEXT,
    linkedin_url    TEXT,
    job_title       TEXT,
    company_name    TEXT,
    company_domain  TEXT,
    country         TEXT,
    city            TEXT,
    -- Datos internos
    product_target  TEXT NOT NULL, -- 'shieldai' | 'twolaps'
    status          TEXT NOT NULL DEFAULT 'new',
        -- new → drafted → sent → followed_up_1 → followed_up_2 → replied → meeting → closed
    touchpoints     INTEGER DEFAULT 0,
    last_contact_at TIMESTAMPTZ,
    next_contact_at TIMESTAMPTZ,
    -- Contenido generado
    draft_subject   TEXT,
    draft_body      TEXT,
    draft_channel   TEXT,         -- 'email' | 'linkedin'
    -- Tracking
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    notes           TEXT
);

CREATE INDEX idx_prospects_status ON prospects(status);
CREATE INDEX idx_prospects_product ON prospects(product_target);
CREATE INDEX idx_prospects_next_contact ON prospects(next_contact_at);
CREATE INDEX idx_prospects_email ON prospects(email);
```

---

## Configuración — config.py

```python
# ══════════════════════════════════════════════════════════════
# ICP FILTERS (Apollo People API Search)
# ══════════════════════════════════════════════════════════════

ICP_SHIELDAI = {
    "person_titles": [
        "CISO", "Chief Information Security Officer",
        "CTO", "Chief Technology Officer",
        "DPO", "Data Protection Officer",
        "VP Security", "VP IT", "Head of IT",
        "Director of Information Security",
        "IT Security Manager", "Cybersecurity Manager"
    ],
    "employee_ranges": ["25-50", "51-200", "201-500"],
    "person_locations": ["Spain", "Mexico", "Colombia", "Argentina", "Chile"],
    "q_keywords": "",  # Dejar vacío o añadir tech keywords
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
    "cold_email": 0,              # Día 0: primer email
    "linkedin_connect": 3,        # Día 3: connection request
    "follow_up_1": 7,             # Día 7: follow-up email
    "follow_up_2": 14,            # Día 14: último intento
    "max_touchpoints": 4,         # Máximo intentos
    "min_days_between": 3,        # Mínimo días entre contactos
}

# ══════════════════════════════════════════════════════════════
# LÍMITES DIARIOS
# ══════════════════════════════════════════════════════════════

DAILY_LIMITS = {
    "new_prospects": 50,          # Máximo nuevos prospects/día
    "claude_calls": 30,           # Máximo generaciones/día
    "emails_sent": 50,            # Máximo emails/día
    "linkedin_requests": 20,      # Máximo requests/día
}

# ══════════════════════════════════════════════════════════════
# PRODUCTO → DESCRIPCIÓN (para el prompt de Claude)
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
```

---

## Módulos — Lógica

### 1. prospector.py

```
FLUJO:
1. Cargar ICP de config según product (ShieldAI o 2laps)
2. Llamar Apollo People Search API:
   POST https://api.apollo.io/api/v1/mixed_people/search
   Headers: { "x-api-key": APOLLO_API_KEY }
   Body: {
     "person_titles": [...],
     "employee_ranges": [...],
     "person_locations": [...],
     "page": 1,
     "per_page": 50
   }
3. Para cada resultado, verificar si ya existe en DB (dedup por apollo_id o email)
4. Si es nuevo → enriquecer con People Enrichment para obtener email verificado
   POST https://api.apollo.io/api/v1/people/match
   Body: {
     "first_name": "...",
     "last_name": "...",
     "organization_name": "...",
     "reveal_personal_emails": false,
     "reveal_phone_number": false
   }
5. INSERT en tabla prospects con status='new'
6. Respetar DAILY_LIMITS["new_prospects"]
7. Rotar páginas de Apollo entre ejecuciones (guardar last_page en DB o archivo)

NOTA: People API Search devuelve hasta 50.000 resultados (100/página, 500 páginas).
      Ir paginando día a día. Guardar el page offset en un archivo local o tabla config.
```

### 2. composer.py

```
FLUJO:
1. SELECT * FROM prospects WHERE status = 'new' LIMIT {DAILY_LIMITS["claude_calls"]}
2. Para cada prospect:
   a. Cargar template según product_target + touchpoint number
   b. Rellenar variables: {nombre}, {empresa}, {cargo}, {industria}, {producto_desc}
   c. Llamar Claude API:
      POST https://api.anthropic.com/v1/messages
      Headers: {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01"
      }
      Body: {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 500,
        "messages": [{"role": "user", "content": prompt_rellenado}]
      }
   d. Parsear respuesta → extraer subject y body
   e. UPDATE prospect SET draft_subject=..., draft_body=..., status='drafted'
3. Logging de cada generación

PROMPT TEMPLATE (ejemplo shieldai_cold.txt):
---
Genera un cold email en español para {first_name} {last_name},
{job_title} en {company_name} ({industry}, {company_size} empleados).

Producto: {product_description}

Reglas:
- Máximo 5 líneas de cuerpo (sin contar saludo ni firma)
- Primera línea: hook personalizado a su cargo/industria, sin peloteo
- Tono directo y profesional, sin buzzwords ni "en el panorama actual"
- CTA = responder al email o reservar 15 min: {calendly_url}
- Firma: Rodrigo Quesada · Director Nuevos Negocios · Truco y Trufa
- NO incluir asunto genérico tipo "Propuesta" — que sea específico

Responde SOLO con el email en este formato exacto:
SUBJECT: [asunto aquí]
BODY: [cuerpo aquí]
---
```

### 3. sender.py

```
FLUJO:
1. SELECT * FROM prospects
   WHERE status = 'drafted'
   AND draft_channel = 'email'
   ORDER BY created_at ASC
   LIMIT {DAILY_LIMITS["emails_sent"]}
2. Para cada prospect con email:
   a. Enviar via Unipile:
      POST https://{DSN}.unipile.com:13443/api/v1/emails
      Headers: { "X-API-KEY": UNIPILE_API_KEY }
      Body: {
        "account_id": "{email_account_id}",
        "to": [{"email": prospect.email, "display_name": prospect.first_name}],
        "subject": prospect.draft_subject,
        "body": prospect.draft_body
      }
   b. UPDATE prospect SET status='sent', touchpoints=touchpoints+1,
      last_contact_at=NOW(),
      next_contact_at=NOW() + interval '{CADENCE["follow_up_1"]} days'
3. Para LinkedIn (si tiene linkedin_url y touchpoints permite):
   a. Enviar connection request via Unipile:
      POST https://{DSN}.unipile.com:13443/api/v1/users/invite
      Body: {
        "account_id": "{linkedin_account_id}",
        "provider_id": "{linkedin_profile_id}",
        "message": "Hola {first_name}, [nota corta personalizada]"
      }
   b. UPDATE touchpoints, last_contact_at
4. Espaciar envíos: time.sleep(random.uniform(60, 180)) entre cada uno
   (para no disparar spam filters)

IMPORTANTE:
- NUNCA enviar todos a la vez. Espaciar a lo largo del día.
- Respetar: max 50 emails/día, max 20 LinkedIn requests/día
- Si es fin de semana, no enviar (nadie lee cold emails el sábado)
```

### 4. follower.py

```
FLUJO:
1. Revisar respuestas via Unipile:
   GET https://{DSN}.unipile.com:13443/api/v1/emails?folder=inbox&limit=50
   - Filtrar por emails que son respuesta a nuestros envíos
   - Si alguien responde → UPDATE status='replied', notes=respuesta
   - Notificar a Rodrigo (email o Telegram bot)

2. Generar follow-ups:
   SELECT * FROM prospects
   WHERE status IN ('sent', 'followed_up_1')
   AND next_contact_at <= NOW()
   AND touchpoints < {CADENCE["max_touchpoints"]}
   - Para cada uno → composer genera nuevo draft con template follow-up
   - UPDATE status='drafted' (vuelve al ciclo de sender.py)

3. Limpiar prospects muertos:
   - Si touchpoints >= max_touchpoints y no hay respuesta → status='exhausted'
   - Esos no se vuelven a tocar
```

### 5. main.py

```python
"""
Orquestador. Se ejecuta 1 vez al día via cron.
Orden de ejecución importa:
  1. follower  — primero procesar respuestas y generar follow-ups
  2. prospector — buscar nuevos prospects
  3. composer  — generar drafts para todos los pendientes
  4. sender    — enviar todo lo que está drafted
"""

import logging
from datetime import datetime

from follower import check_replies, generate_followups
from prospector import find_new_prospects
from composer import generate_drafts
from sender import send_emails, send_linkedin_requests

logging.basicConfig(filename='logs/outreach.log', level=logging.INFO)

def run():
    today = datetime.now()

    # No ejecutar fines de semana
    if today.weekday() >= 5:
        logging.info("Weekend — skipping")
        return

    logging.info(f"=== Outreach run: {today.isoformat()} ===")

    # 1. Procesar respuestas
    replies = check_replies()
    logging.info(f"Replies found: {replies}")

    # 2. Generar follow-ups para los que toca
    followups = generate_followups()
    logging.info(f"Follow-ups queued: {followups}")

    # 3. Buscar nuevos prospects
    new = find_new_prospects(product="shieldai", limit=25)
    new += find_new_prospects(product="twolaps", limit=25)
    logging.info(f"New prospects: {new}")

    # 4. Generar drafts
    drafts = generate_drafts()
    logging.info(f"Drafts generated: {drafts}")

    # 5. Enviar
    sent_email = send_emails()
    sent_li = send_linkedin_requests()
    logging.info(f"Sent: {sent_email} emails, {sent_li} LinkedIn")

if __name__ == "__main__":
    run()
```

---

## Setup — Paso a paso

### Paso 1: Crear cuentas y obtener API keys

```
□ Apollo.io → Plan Professional ($79/mes)
  → Settings → API Keys → Create Master Key
  → Guardar como APOLLO_API_KEY

□ Neon (neon.tech) → Crear proyecto "tt-outreach"
  → Dashboard → Connection string (postgres://...)
  → Guardar como DATABASE_URL

□ Anthropic → Console → API Keys → Create Key
  → Guardar como ANTHROPIC_API_KEY

□ Unipile (unipile.com) → Registrarse
  → Conectar cuenta Gmail (la que usas para outreach)
  → Conectar cuenta LinkedIn
  → Dashboard → API Key + DSN
  → Guardar como UNIPILE_API_KEY y UNIPILE_DSN
  → Anotar account_id de email y LinkedIn
```

### Paso 2: Configurar .env

```env
APOLLO_API_KEY=xxxxx
DATABASE_URL=postgres://user:pass@ep-xxx.eu-central-1.aws.neon.tech/neondb?sslmode=require
ANTHROPIC_API_KEY=sk-ant-xxxxx
UNIPILE_API_KEY=xxxxx
UNIPILE_DSN=xxxxx
UNIPILE_EMAIL_ACCOUNT_ID=xxxxx
UNIPILE_LINKEDIN_ACCOUNT_ID=xxxxx
CALENDLY_URL=https://calendly.com/rodrigo-quesada-trucoytrufa/30min
```

### Paso 3: Instalar dependencias

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Paso 4: Crear tablas en Neon

```bash
# Conectar con psql o desde la consola de Neon y ejecutar el SQL del schema
psql $DATABASE_URL -f schema.sql
```

### Paso 5: Test individual de cada módulo

```bash
# Probar Apollo
python prospector.py --test --product shieldai --limit 5

# Probar Claude
python composer.py --test --limit 3

# Probar Unipile (enviar a tu propio email primero)
python sender.py --test --to rodrigo@trucoytrufa.com

# Probar follower
python follower.py --test
```

### Paso 6: Configurar cron

```bash
# Ejecutar cada día a las 8:00 AM (hora de Madrid)
crontab -e

# Añadir:
0 8 * * 1-5 cd /ruta/al/proyecto && /ruta/al/venv/bin/python main.py >> logs/cron.log 2>&1
```

---

## Cadencia visual

```
Día 0  ──▶  📧 Cold email
Día 3  ──▶  🔗 LinkedIn connection request (si tiene perfil)
Día 7  ──▶  📧 Follow-up 1 (si no ha respondido)
Día 14 ──▶  📧 Follow-up 2 / último intento (ángulo diferente)
Día 14+──▶  ❌ Status = exhausted (no más contacto)

Si responde en cualquier punto ──▶ ✅ Status = replied, notificar a Rodrigo
```

---

## Métricas esperadas (mes 1)

| Métrica | Estimación conservadora |
|---|---|
| Prospects contactados/mes | 750-1.000 |
| Tasa de apertura email | 30-40% |
| Tasa de respuesta | 2-3% |
| Conversaciones generadas | 15-30 |
| Reuniones cerradas | 3-9 |
| Coste por reunión | €15-45 |

---

## Notas importantes

1. **Warmup del email**: Si la cuenta Gmail es nueva o poco usada, hacer warmup 2 semanas antes. Enviar emails reales a contactos que te respondan. Si no, tus cold emails van a spam.

2. **LinkedIn safety**: No pasar de 20 requests/día. Las cuentas nuevas empezar con 10/día la primera semana. LinkedIn bastiona el rate limiting, pero ser conservador.

3. **GDPR**: Estamos en España. Los emails B2B a direcciones corporativas tienen base legal de interés legítimo, pero hay que incluir opción de baja en cada email. Añadir al footer: "Si prefieres no recibir más emails, responde 'baja' y te elimino inmediatamente."

4. **Rotación de ángulos**: Cada touchpoint debe tener un ángulo diferente. No repetir el mismo pitch. Ejemplo para ShieldAI:
   - Cold: "Tu equipo ya usa ChatGPT, ¿sabes qué datos están pegando ahí?"
   - FU1: "Un dato: el 40% de empleados pega datos internos en ChatGPT sin saberlo"
   - FU2: "Último mensaje — si no es prioridad ahora, lo entiendo. Dejo el enlace por si acaso"

5. **No enviar desde tu email personal**: Crear una cuenta tipo outreach@trucoytrufa.com o rodrigo@trucoytrufa.com dedicada. Así si la queman en spam, no afecta a tu email principal.

6. **Iterar los prompts**: Las primeras 50 emails van a ser mediocres. Revisa manualmente, ajusta los prompts, vuelve a probar. Después de 100, ya deberían salir buenos solos.
