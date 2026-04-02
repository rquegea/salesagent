# Setup Detallado — T&T Outreach Agent

## Paso 1: Crear cuenta Supabase y obtener DATABASE_URL

1. Ve a https://supabase.com
2. Sign up con tu email
3. Crea un nuevo proyecto
4. En el dashboard, ve a `Settings → Database → Connection Pooling`
5. Copia el connection string (asegúrate de que es PostgreSQL, no pgBouncer)
6. Reemplaza `[YOUR-PASSWORD]` con la contraseña que elegiste

```
postgres://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres
```

## Paso 2: Obtener ANTHROPIC_API_KEY

1. Ve a https://console.anthropic.com
2. Sign up o inicia sesión
3. Ve a `API Keys`
4. Crea una nueva API key
5. Cópiala (se mostrará solo una vez)

## Paso 3: Configurar Unipile

1. Ve a https://unipile.com
2. Sign up
3. Conecta tu cuenta Gmail (la que usarás para outreach)
   - En dashboard, ve a "Accounts"
   - Click "Connect Gmail"
   - Autoriza acceso
4. Conecta tu cuenta LinkedIn
   - Mismo proceso
5. En dashboard, obtén:
   - API Key (en Settings)
   - DSN (en Settings)
   - Email Account ID (en Accounts, bajo Gmail)
   - LinkedIn Account ID (en Accounts, bajo LinkedIn)

## Paso 4: Preparar el proyecto

```bash
# Clonar/navegar al proyecto
cd tt-outreach-agent

# Crear virtual environment
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## Paso 5: Configurar .env

```bash
# Copiar template
cp .env.example .env

# Editar con tus valores
nano .env
```

Rellena todas las variables:

```env
APOLLO_API_KEY=4xuYClyzqNB_HtqYzvrcpQ

DATABASE_URL=postgres://postgres:PASSWORD@db.xxx.supabase.co:5432/postgres

ANTHROPIC_API_KEY=sk-ant-xxxxx

UNIPILE_API_KEY=xxxxx
UNIPILE_DSN=xxxxx
UNIPILE_EMAIL_ACCOUNT_ID=xxxxx
UNIPILE_LINKEDIN_ACCOUNT_ID=xxxxx

CALENDLY_URL=https://calendly.com/rodrigo-quesada-trucoytrufa/30min
```

## Paso 6: Inicializar base de datos

```bash
source venv/bin/activate

# Esto creará las tablas
python -c "from db import init_db; init_db()"
```

Deberías ver:
```
Database initialized successfully
```

## Paso 7: Test de cada módulo

### Test Apollo prospector

```bash
python prospector.py --test --product shieldai --limit 5
```

Debería retornar:
```
INFO:root:Apollo search returned X prospects
INFO:root:Found X new prospects for shieldai
```

### Test Claude composer

```bash
python composer.py --test --limit 3
```

Debería generar 3 drafts.

### Test Unipile sender (dry run)

```bash
python sender.py --test --dry-run
```

Debería mostrar:
```
[DRY RUN] Would send: [SUBJECT] to email@example.com
```

### Test follower

```bash
python follower.py --test
```

## Paso 8: Ejecutar manualmente

```bash
source venv/bin/activate
python main.py
```

Deberías ver:
```
=== Outreach run: 2025-04-02T08:00:00 ===
Step 1: Checking replies...
Step 2: Generating follow-ups...
Step 3: Searching new prospects...
...
=== Outreach run completed successfully ===
```

## Paso 9: Configurar cron (macOS/Linux)

```bash
# Abre el editor de cron
crontab -e

# Añade esta línea (ejecuta a las 8:00 AM, lunes a viernes):
0 8 * * 1-5 cd /Users/macbook/salesagent/tt-outreach-agent && /Users/macbook/salesagent/tt-outreach-agent/venv/bin/python main.py >> logs/cron.log 2>&1
```

Verifica que funcionó:
```bash
crontab -l
```

## Paso 10: Email warmup (IMPORTANTE)

**Antes de enviar cold emails masivos:**

1. La cuenta Gmail debe tener 2 semanas de actividad
2. Envía emails reales a contactos que probablemente respondan
3. Espera a tener respuestas positivas
4. Entonces empieza con los cold emails

Sin warmup, irás a spam.

## Verificación

### Ver logs
```bash
tail -f logs/outreach.log
```

### Ver base de datos (Supabase console)
1. Ve a https://app.supabase.com
2. Selecciona tu proyecto
3. SQL Editor
4. Ejecuta:
```sql
SELECT id, first_name, email, status, touchpoints
FROM prospects
LIMIT 10;
```

### Ver estadísticas
```bash
python -c "from db import get_stats; import json; print(json.dumps(get_stats(), indent=2, default=str))"
```

## Troubleshooting

### "psycopg2 connection error"
- Verifica que DATABASE_URL es correcto
- Verifica que Supabase está en tu IP whitelist (Settings → Network)
- Intenta conexión manual: `psql "postgres://..."`

### "ANTHROPIC_API_KEY invalid"
- Copia de nuevo desde console.anthropic.com
- Verifica que no hay espacios

### "Unipile API error"
- Verifica que las credenciales son correctas
- Verifica que Gmail/LinkedIn están conectados en Unipile dashboard

### "No prospects found"
- Verifica APOLLO_API_KEY
- Intenta manualmente: `python prospector.py --test --product shieldai --limit 1`

### Cron no ejecuta
- Verifica con: `log stream --level debug --predicate 'eventMessage contains[c] cron'`
- O revisa si hay errores: `cat logs/cron.log`

## Siguientes pasos

1. **Iterar prompts**: Las primeras 50 emails van a ser mediocres. Revisa manualmente y ajusta templates.
2. **Monitorear respuestas**: Revisa logs diariamente.
3. **Validar email warmup**: Espera 2 semanas antes de escalar volumen.
4. **Optimizar cadencia**: Ajusta CADENCE en config.py según resultados.
