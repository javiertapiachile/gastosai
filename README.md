# GastosAI

Dashboard local de análisis de gastos personales con clasificación automática por IA.

## ¿Qué hace?

- Importa extractos bancarios en formato `.xlsx`, `.csv` o `.pdf`
- Interpreta nombres crípticos de comercios (`MCD #3421` → McDonald's)
- Clasifica cada transacción automáticamente usando un LLM
- Muestra KPIs, gráfico de torta y evolución mensual
- Corre **100% local** — tus datos nunca salen de tu equipo

## Requisitos

- Docker Desktop (incluye Docker Compose)
- Una API key de Anthropic, OpenAI **o** Ollama corriendo localmente

## Setup en 3 pasos

### 1. Clonar y configurar variables de entorno

```bash
git clone https://github.com/tu-usuario/gastosai.git
cd gastosai
cp .env.example .env
```

Edita `.env` con tu proveedor y API key:

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### 2. Levantar con Docker Compose

```bash
docker compose up --build
```

La primera vez descarga imágenes y construye los contenedores (~2-3 minutos).

### 3. Abrir el dashboard

- **Frontend:** http://localhost:5173
- **API docs:** http://localhost:8000/docs

---

## Proveedores LLM soportados

| Proveedor | Variable | Modelo usado |
|-----------|----------|--------------|
| Anthropic | `ANTHROPIC_API_KEY` | claude-3-5-haiku-latest |
| OpenAI | `OPENAI_API_KEY` | gpt-4o-mini |
| Ollama | `OLLAMA_BASE_URL` | configurable vía `OLLAMA_MODEL` |

### Usar con Ollama (sin costos de API)

1. Instalar [Ollama](https://ollama.ai) en tu máquina
2. Descargar un modelo: `ollama pull llama3`
3. En `.env`: `LLM_PROVIDER=ollama`
4. `docker compose up`

---

## Estructura del proyecto

```
gastosai/
├── docker-compose.yml
├── .env.example
├── backend/              # FastAPI + SQLAlchemy
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/          # Migraciones de base de datos
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── models/       # Modelos SQLAlchemy
│       ├── schemas/      # Schemas Pydantic
│       ├── routers/      # Endpoints de la API
│       └── crud/         # Lógica de acceso a datos
└── frontend/             # React + Vite
    ├── Dockerfile
    └── src/
        ├── api/          # Cliente HTTP
        ├── components/   # Componentes reutilizables
        ├── pages/        # Páginas principales
        └── styles/       # Variables CSS
```

## Comandos útiles

```bash
# Ver logs en tiempo real
docker compose logs -f

# Solo logs del backend
docker compose logs -f backend

# Detener todo
docker compose down

# Detener y borrar datos (¡cuidado!)
docker compose down -v

# Reconstruir solo el frontend
docker compose build frontend && docker compose up frontend
```

## API endpoints

| Método | Path | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado del sistema |
| GET | `/api/v1/transactions/` | Listar transacciones (paginado) |
| GET | `/api/v1/transactions/kpis` | KPIs del dashboard |
| GET | `/api/v1/transactions/charts/por-categoria` | Datos para gráfico torta |
| GET | `/api/v1/transactions/charts/evolucion-mensual` | Evolución mensual |
| PATCH | `/api/v1/transactions/{id}` | Editar categoría manualmente |
| GET | `/api/v1/categories/` | Listar categorías |
| POST | `/api/v1/categories/` | Crear categoría |
| POST | `/api/v1/uploads/` | Subir archivo (inicia clasificación) |
| GET | `/api/v1/uploads/{id}` | Estado de procesamiento |

Documentación interactiva completa en http://localhost:8000/docs

## Privacidad

- La base de datos SQLite vive en un volumen Docker local (`gastosai_data`)
- Solo las descripciones de transacciones (sin montos, sin RUTs) se envían al LLM para clasificación
- El caché SQLite evita enviar la misma descripción dos veces
