# Quickstart — 10 minutos

## 1. Clonar/navegar

```bash
cd /Users/macbook/salesagent/tt-outreach-agent
```

## 2. Crear virtualenv

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Configurar .env

```bash
cp .env.example .env
# Editar con tus credenciales (solo DATABASE_URL, ANTHROPIC_API_KEY, UNIPILE_*)
# APOLLO_API_KEY ya está incluida
```

Necesitas:
- `DATABASE_URL` — De Supabase
- `ANTHROPIC_API_KEY` — De Anthropic
- `UNIPILE_API_KEY`, `UNIPILE_DSN`, `UNIPILE_EMAIL_ACCOUNT_ID`, `UNIPILE_LINKEDIN_ACCOUNT_ID` — De Unipile

## 4. Inicializar BD

```bash
python -c "from db import init_db; init_db()"
# Deberías ver: "Database initialized successfully"
```

## 5. Test rápido

```bash
# Prospector
python prospector.py --test --product shieldai --limit 2

# Composer
python composer.py --test --limit 1

# Sender (dry run)
python sender.py --test --dry-run
```

## 6. Ver logs

```bash
tail -f logs/outreach.log
```

## 7. Ejecutar (manual)

```bash
python main.py
```

Verás algo como:
```
=== Outreach run: 2025-04-02T11:30:00 ===
Step 1: Checking replies...
Step 2: Generating follow-ups...
...
=== Outreach run completed successfully ===
```

## 8. Configurar cron (opcional, para automatización)

```bash
crontab -e

# Añadir:
0 8 * * 1-5 cd /Users/macbook/salesagent/tt-outreach-agent && /Users/macbook/salesagent/tt-outreach-agent/venv/bin/python main.py >> logs/cron.log 2>&1
```

## Troubleshooting rápido

| Error | Solución |
|---|---|
| "DATABASE_URL not set" | Verifica .env existe y tiene DATABASE_URL |
| "APOLLO_API_KEY not set" | Verifica .env |
| "psycopg2 connection error" | Verifica DATABASE_URL es correcto |
| "No prospects found" | APOLLO_API_KEY podría ser inválida |
| "No templates found" | Verifica archivos en templates/ |

## Documentación completa

- **README.md** — Uso general
- **SETUP.md** — Setup detallado (30-60 min)
- **STRUCTURE.md** — Arquitectura completa
- **CLAUDE.md** — Concepto del proyecto

## Checklist de setup

- [ ] Supabase DB creada y DATABASE_URL copiada
- [ ] Anthropic API key obtenida
- [ ] Unipile cuenta creada, email/LinkedIn conectados, credenciales copiadas
- [ ] .env configurado con todas las variables
- [ ] `pip install -r requirements.txt` ejecutado
- [ ] `python -c "from db import init_db; init_db()"` ejecutado sin errores
- [ ] Test prospector, composer, sender sin errores
- [ ] main.py ejecutado manualmente sin errores
- [ ] Cron configurado (opcional)

## Próximos pasos

1. **Email warmup** — 2 semanas de actividad normal antes de cold emails
2. **Monitorear logs** — Ver cómo van los primeros 50 emails
3. **Iterar prompts** — Ajustar templates según calidad
4. **Escalar volumen** — Aumentar DAILY_LIMITS después de validar
