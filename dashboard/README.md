# T&T Outreach Dashboard

Dashboard en tiempo real para el sistema de outreach automatizado de Truco y Trufa.

## Stack

- **React 18** — Frontend framework
- **Vite** — Build tool
- **Tailwind CSS** — Estilos minimalistas tipo Apple
- **Supabase** — Base de datos Postgres

## Features

✨ **Vista general** — Métricas en tiempo real (total prospects, drafts, enviados, respuestas, tasa de respuesta), gráfico de actividad últimos 7 días

👥 **Tabla de prospects** — Listado completo filtrable por status (new, drafted, sent, replied, exhausted), producto (shieldai/twolaps), con búsqueda por nombre/empresa/email

🔍 **Detalle de prospect** — Email generado, historial de touchpoints, timeline de cadencia, notas

📬 **Cola de envío** — Ver borradores pendientes, editar antes de enviar, aprobar o descartar

⚡ **Log de actividad** — Últimos eventos (emails enviados, respuestas, nuevos prospects), filtrable por tipo

## Setup

### 1. Instalar dependencias

```bash
cd dashboard
npm install
```

### 2. Variables de entorno

Crea un archivo `.env.local` con tu URL y clave de Supabase:

```env
VITE_SUPABASE_URL=https://nnehagxifkhhkmnejbwk.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGc...
```

### 3. Ejecutar en desarrollo

```bash
npm run dev
```

La app se abrirá en http://localhost:5173

### 4. Build para producción

```bash
npm run build
npm run preview
```

## Estructura

```
src/
├── components/
│   ├── Navigation.jsx        — Navbar con navegación
│   ├── Overview.jsx          — Dashboard principal con stats
│   ├── ProspectsTable.jsx    — Tabla filtrable
│   ├── ProspectDetail.jsx    — Detalle de un prospect
│   ├── SendQueue.jsx         — Cola de borradores
│   └── ActivityLog.jsx       — Log de actividad
├── lib/
│   └── supabase.js          — Queries y conexión
├── App.jsx                   — Componente principal
├── main.jsx                  — Entry point
└── index.css                 — Tailwind + estilos globales
```

## Uso

### Dashboard (Vista general)

- Métricas en tiempo real
- Gráfico de actividad por día
- Distribución por producto y status

### Prospects

- Tabla con todos los prospects
- Filtrar por: status, producto, búsqueda libre
- Click en una fila para ver detalles

### Detalle

- Información de contacto completo
- Email generado (asunto + cuerpo)
- Timeline de cadencia (qué touchpoints se han hecho)
- Cambiar status desde aquí

### Cola de envío

- Todos los borradores listos para enviar
- Editar asunto/cuerpo antes de aprobar
- Aprobar y enviar, o descartar

### Actividad

- Últimos eventos del sistema
- Filtrar por tipo (sent, replied, drafted, new)
- Timestamps relativos (hace 5 minutos, hace 2 horas, etc)

## Performance

- Supabase auto-carga datos en tiempo real
- Las vistas se refrescan automáticamente cada 30s (overview) o 10s (activity log)
- Interfaz minimalista sin dependencias pesadas
- Webpack + Tree shaking para bundle minimal
