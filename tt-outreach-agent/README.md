# T&T Outreach Agent

Sistema automatizado de prospección y outreach B2B para Truco y Trufa.

## Setup rápido

### 1. Instalar dependencias

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar .env

Copia `.env.example` a `.env` y rellena las credenciales:

```bash
cp .env.example .env
# Edita .env con tus API keys
```

Variables necesarias:
- `APOLLO_API_KEY` — Apollo.io (ya incluida)
- `DATABASE_URL` — Supabase Postgres
- `ANTHROPIC_API_KEY` — Claude API
- `UNIPILE_API_KEY` — Unipile API
- `UNIPILE_DSN` — Unipile DSN
- `UNIPILE_EMAIL_ACCOUNT_ID` — ID de cuenta email
- `UNIPILE_LINKEDIN_ACCOUNT_ID` — ID de cuenta LinkedIn
- `CALENDLY_URL` — Tu enlace Calendly

### 3. Inicializar base de datos

```bash
python -c "from db import init_db; init_db()"
```

### 4. Test individual de módulos

```bash
# Test prospector
python prospector.py --test --product shieldai --limit 5

# Test composer
python composer.py --test --limit 3

# Test sender
python sender.py --test --dry-run

# Test follower
python follower.py --test
```

### 5. Configurar cron (macOS/Linux)

```bash
crontab -e

# Añadir (8:00 AM Madrid time, lunes a viernes):
0 8 * * 1-5 cd /ruta/al/proyecto && /ruta/al/venv/bin/python main.py >> logs/cron.log 2>&1
```

## Uso

### Ejecutar manualmente

```bash
python main.py
```

### Ver logs

```bash
tail -f logs/outreach.log
```

## Estructura

```
tt-outreach-agent/
├── main.py              # Orquestador principal
├── prospector.py        # Busca prospects en Apollo
├── composer.py          # Genera drafts con Claude
├── sender.py            # Envía emails/LinkedIn
├── follower.py          # Monitorea respuestas
├── db.py               # Conexión a Supabase
├── config.py           # Configuración global
├── templates/          # Prompts para Claude
│   ├── shieldai_cold.txt
│   ├── shieldai_fu1.txt
│   ├── shieldai_fu2.txt
│   ├── twolaps_cold.txt
│   ├── twolaps_fu1.txt
│   └── twolaps_fu2.txt
└── logs/               # Logs de ejecución
    └── outreach.log
```

## Flujo diario

1. **Follower** — Procesa respuestas y genera follow-ups
2. **Prospector** — Busca nuevos prospects en Apollo (50/día)
3. **Composer** — Genera drafts con Claude (30/día)
4. **Sender** — Envía emails (50/día) + LinkedIn (20/día)

## Estados de prospect

- `new` — Nuevo, sin draft
- `drafted` — Draft generado, pendiente envío
- `sent` — Enviado
- `followed_up_1` — Follow-up 1 enviado
- `followed_up_2` — Follow-up 2 enviado
- `replied` — Ha respondido
- `meeting` — Reunión agendada
- `closed` — Cerrado
- `exhausted` — Sin más intentos

## Cadencia

| Touchpoint | Día | Acción |
|---|---|---|
| 0 | 0 | Cold email |
| 1 | 3 | LinkedIn connection |
| 2 | 7 | Follow-up 1 |
| 3 | 14 | Follow-up 2 (último) |

## Notas importantes

- **Email warmup**: Nueva cuenta necesita 2 semanas de warmup
- **LinkedIn safety**: Max 20 requests/día para cuentas nuevas
- **GDPR**: Opción de baja en cada email
- **Rotación de ángulos**: Cada touchpoint con ángulo diferente

## Troubleshooting

### "APOLLO_API_KEY not set"
Asegúrate de que `.env` está correctamente configurado y que has hecho `source venv/bin/activate`.

### "Database connection failed"
Verifica que `DATABASE_URL` es válido y tiene acceso desde tu red.

### "No templates found"
Los archivos en `templates/` deben estar presentes. Verifica la ruta.

### Emails van a spam
Si la cuenta email es nueva, necesita warmup de 2 semanas. Envía emails reales a contactos que respondan primero.

## Métricas esperadas (mes 1)

- 750-1000 prospects contactados
- 30-40% open rate
- 2-3% reply rate
- €15-45 por reunión cerrada
