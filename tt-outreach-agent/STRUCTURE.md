# Estructura del Proyecto — T&T Outreach Agent

## Descripción general

Sistema automatizado de prospección y outreach B2B que contacta 25-50 empresas/día para dos productos: **ShieldAI** (extensión Chrome DLP) y **2laps** (GEO/AI visibility monitoring).

**Stack:**
- Base de datos: Supabase (PostgreSQL)
- IA: Claude API (Sonnet 4)
- Email/LinkedIn: Unipile API
- Lenguaje: Python 3.11+
- Ejecución: Cron local o VPS

---

## Archivos y módulos

### Archivos de configuración

#### `.env.example`
Template de variables de entorno. Cópialo a `.env` y rellena con tus credenciales.
```
APOLLO_API_KEY=4xuYClyzqNB_HtqYzvrcpQ
DATABASE_URL=postgres://...
ANTHROPIC_API_KEY=sk-ant-...
UNIPILE_API_KEY=...
CALENDLY_URL=https://...
```

#### `.env`
**NO commitear.** Archivo real con credenciales. Ignorado por `.gitignore`.

#### `.gitignore`
Especifica qué archivos ignorar en git (env, logs, __pycache__, etc).

#### `requirements.txt`
Dependencias Python:
- `requests` — HTTP requests
- `psycopg2-binary` — PostgreSQL driver
- `anthropic` — Claude API SDK
- `python-dotenv` — Cargar .env

---

### Módulos principales

#### `config.py`
Configuración global:
- **ICP_SHIELDAI** — Filtros para buscar prospects de ShieldAI (CISO, CTO, etc)
- **ICP_TWOLAPS** — Filtros para 2laps (CMO, Head of Marketing, etc)
- **CADENCE** — Tiempos entre contactos (día 0: cold, día 3: LinkedIn, día 7: FU1, día 14: FU2)
- **DAILY_LIMITS** — Límites de ejecución (50 nuevos prospects, 30 drafts, 50 emails, 20 LinkedIn)
- **PRODUCT_DESCRIPTIONS** — Descripciones para los prompts de Claude

#### `db.py`
Capa de acceso a datos:
- `init_db()` — Crear tablas si no existen
- `insert_prospect()` — Añadir nuevo prospect
- `get_prospects_by_status()` — Obtener prospects por estado
- `update_prospect_draft()` — Guardar draft generado
- `update_prospect_sent()` — Marcar como enviado
- `check_prospect_exists()` — Deduplicación
- `get_stats()` — Estadísticas globales

**Tabla `prospects`:**
- Datos de contacto: first_name, last_name, email, linkedin_url, job_title, company_name
- Datos internos: product_target, status, touchpoints, last_contact_at, next_contact_at
- Contenido: draft_subject, draft_body, draft_channel
- Metadatos: created_at, updated_at, notes

**Tabla `config`:**
- Almacena estado (ej: `apollo_page_shieldai` → 5 para rastrear paginación)

#### `prospector.py`
Busca nuevos prospects:
- `search_apollo()` — Llama Apollo People Search API con ICP filters
- `enrich_prospect()` — Obtiene email verificado vía Apollo People Match
- `find_new_prospects()` — Orquestación: busca, deduplica, enriquece, inserta

**Flujo:**
1. Obtiene ICP para producto (ShieldAI/2laps)
2. Busca en Apollo con person_titles, employee_ranges, locations
3. Para cada resultado, verifica si existe (dedup por email/apollo_id)
4. Si no existe y tiene email, lo inserta en DB con status='new'
5. Rastrea página actual en tabla config (para no repetir)

**Límite:** 50 nuevos/día

#### `composer.py`
Genera drafts de email con Claude:
- `load_template()` — Lee archivo de template (.txt)
- `render_template()` — Sustituye variables: {first_name}, {product_description}, etc
- `call_claude()` — Llama Claude API (Sonnet 4)
- `parse_email()` — Parsea respuesta SUBJECT/BODY
- `generate_draft_for_prospect()` — Genera draft para un prospect
- `generate_drafts()` — Orquestación para todos los nuevos

**Flujo:**
1. Obtiene prospects con status='new' (límite 30/día)
2. Para cada uno, determina tipo de template según touchpoints (cold/fu1/fu2)
3. Carga template de archivo (ej: shieldai_cold.txt)
4. Sustituye variables con datos del prospect
5. Llama Claude con el prompt personalizado
6. Parsea "SUBJECT: X\nBODY: Y"
7. Actualiza DB con draft_subject, draft_body, status='drafted'

**Límite:** 30 drafts/día

#### `sender.py`
Envía emails y conexiones LinkedIn:
- `send_email_unipile()` — Envía email vía Unipile API
- `send_linkedin_request()` — Envía connection request vía Unipile
- `send_emails()` — Orquestación de emails
- `send_linkedin_requests()` — Orquestación de LinkedIn

**Flujo:**
1. Obtiene prospects con status='drafted'
2. Para cada uno, envía email vía Unipile con GDPR footer
3. Actualiza DB: status='sent', touchpoints+1, next_contact_at=+7días
4. Espera 60-180s entre emails (anti-spam)
5. Si tiene LinkedIn URL, envía connection request

**Límites:**
- 50 emails/día
- 20 LinkedIn requests/día
- No envía fin de semana

#### `follower.py`
Monitorea respuestas y genera follow-ups:
- `check_replies()` — Busca respuestas en inbox vía Unipile
- `generate_followups()` — Marca prospects para follow-up
- `cleanup_exhausted()` — Marca exhaustados (no más intentos)

**Flujo:**
1. Obtiene emails del inbox vía Unipile
2. Identifica respuestas (subject con "Re:")
3. Obtiene prospects que necesitan follow-up (status='sent/followed_up_1' y next_contact_at<=NOW())
4. Para cada uno, llama composer.generate_followup_drafts() (mismo flujo que composer.py)
5. Marca como exhaustados si touchpoints >= 4 y sin respuesta

#### `main.py`
Orquestador principal (cron entry point):
```python
1. init_db() — Asegurar tablas
2. follower.check_replies() — Procesar respuestas
3. follower.generate_followups() — Generar FUs
4. prospector.find_new_prospects() — 25 ShieldAI + 25 2laps
5. composer.generate_drafts() — Generar todos los drafts
6. sender.send_emails() — Enviar emails
7. sender.send_linkedin_requests() — Enviar LinkedIn
8. follower.cleanup_exhausted() — Limpiar agotados
9. Log stats
```

**Ejecutado diariamente a las 8 AM (lunes-viernes) vía cron.**

---

### Templates (prompts de Claude)

Cada template es un prompt que se personaliza con datos del prospect.

#### `templates/shieldai_cold.txt`
Prompt para cold email de ShieldAI. Hook sobre "datos en ChatGPT".

#### `templates/shieldai_fu1.txt`
Follow-up 1 de ShieldAI. Nuevo ángulo: estadísticas ("40% de empleados...").

#### `templates/shieldai_fu2.txt`
Follow-up 2 de ShieldAI (último). Tono: "último mensaje, lo entiendo si no es prioridad".

#### `templates/twolaps_cold.txt`
Prompt para cold email de 2laps. Hook: "¿Cómo aparece tu marca en ChatGPT?"

#### `templates/twolaps_fu1.txt`
Follow-up 1 de 2laps. Nuevo ángulo: competencia/pérdida de visibilidad.

#### `templates/twolaps_fu2.txt`
Follow-up 2 de 2laps (último). Tono respetuoso.

---

### Documentación

#### `README.md`
Setup rápido y guía de uso (10 minutos).

#### `SETUP.md`
Setup detallado paso a paso (30-60 minutos) con troubleshooting.

#### `STRUCTURE.md`
Este archivo. Explicación completa de la arquitectura.

#### `schema.sql`
SQL de las tablas (referencia; se crean automáticamente).

#### `.gitignore`
Archivos a ignorar en git.

---

### Directorios

#### `logs/`
Logs de ejecución.
- `outreach.log` — Log principal (INFO level)
- `cron.log` — Output de cron

#### `templates/`
Prompts para Claude (6 archivos: cold + FU1 + FU2 × 2 productos)

---

## Flujo de ejecución diaria

```
Cron: 8 AM lunes-viernes
    ↓
main.py
    ↓
├─ init_db()
├─ follower.check_replies()
│   └─ check Unipile inbox para respuestas
├─ follower.generate_followups()
│   └─ composer.generate_followup_drafts()
│       └─ Claude: generar FU1/FU2 para due prospects
├─ prospector.find_new_prospects("shieldai", 25)
│   └─ Apollo: buscar, dedup, enriquecer, insertar
├─ prospector.find_new_prospects("twolaps", 25)
├─ composer.generate_drafts()
│   └─ Claude: generar cold emails para nuevos
├─ sender.send_emails()
│   └─ Unipile: enviar 50 emails (con spacing)
├─ sender.send_linkedin_requests()
│   └─ Unipile: enviar 20 connection requests
└─ follower.cleanup_exhausted()
    └─ marcar como exhaustados si touchpoints >= 4
```

---

## Estados de prospect

```
new ────────────→ drafted ────→ sent ─────→ followed_up_1 ─────→ followed_up_2 ─→ exhausted
                     ↑           ↑            ↑
                  Claude API  Unipile API  Claude API
                  (cold email) (email)    (follow-ups)

Si responde en cualquier punto:
    ↓
replied ──→ meeting ──→ closed
```

---

## Configuración y límites

### Límites diarios (config.py)

| Límite | Valor | Razón |
|---|---|---|
| new_prospects | 50 | No saturar BD |
| claude_calls | 30 | Coste API, no repetir prospectos |
| emails_sent | 50 | No trigger spam filter |
| linkedin_requests | 20 | LinkedIn bastiona después de 20/día |

### Cadencia (config.py)

| Día | Acción | Método |
|---|---|---|
| 0 | Cold email | Email |
| 3 | LinkedIn connect | LinkedIn |
| 7 | Follow-up 1 | Email |
| 14 | Follow-up 2 | Email |
| 14+ | Exhaustado | — |

### ICP (Ideal Customer Profile)

**ShieldAI:** CISO, CTO, DPO, VP Security (25-500 empleados, España/LATAM)
**2laps:** CMO, Head of Marketing, VP Marketing (25-500 empleados, España/LATAM)

---

## Integración de APIs

| API | Uso | Módulo |
|---|---|---|
| Apollo.io | Buscar prospects | prospector.py |
| Claude API | Generar emails | composer.py |
| Unipile | Enviar email/LinkedIn | sender.py, follower.py |
| Supabase | BD | db.py |

---

## Métricas esperadas (mes 1)

| Métrica | Estimación |
|---|---|
| Prospects contactados | 750-1000 |
| Open rate | 30-40% |
| Reply rate | 2-3% |
| Conversaciones | 15-30 |
| Reuniones | 3-9 |
| Coste/reunión | €15-45 |

---

## Próximos pasos

1. **Configurar .env** con credenciales reales
2. **Test individual** de cada módulo
3. **Email warmup** 2 semanas antes de escalar
4. **Monitorear logs** los primeros días
5. **Iterar prompts** según calidad de primeros emails
6. **Configurar cron** para automatización
