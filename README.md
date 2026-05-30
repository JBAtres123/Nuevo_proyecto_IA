# EduGrade AI 🎓

**Sistema Inteligente Multimodal para la Calificación Autónoma de Exámenes**

> Gemini 2.0 · RAG + ChromaDB · ICR vía MCP · Consenso 3 Agentes · FastAPI · Vue.js 3

---

## Arquitectura General

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Vue.js 3)                       │
│  HomeView · GradeView · HistoryView · MaterialsView · ConfigView │
└─────────────────────────┬───────────────────────────────────────┘
                           │ HTTP / REST
┌─────────────────────────▼───────────────────────────────────────┐
│                     BACKEND (FastAPI)                            │
│  /upload  /process  /history  /config-exigencia  /materials      │
└──────┬──────────────────┬──────────────────────┬────────────────┘
       │                  │                      │
┌──────▼──────┐  ┌────────▼────────┐  ┌─────────▼──────────┐
│  MCP Server │  │   Agentes IA     │  │  Servicios          │
│  ICR/Vision │  │                  │  │                     │
│  (Gemini)   │  │  ┌─────────────┐ │  │  rag_service.py     │
│             │  │  │Calificador A│ │  │  (ChromaDB +        │
│  Herramien- │  │  └──────┬──────┘ │  │   text-embedding)   │
│  tas MCP:   │  │         │        │  │                     │
│  · extraer_ │  │  ┌──────▼──────┐ │  │  icr_service.py     │
│    texto    │  │  │Calificador B│ │  │  (Gemini Vision)    │
│  · detectar_│  │  └──────┬──────┘ │  │                     │
│    latex    │  │         │        │  │  report_service.py  │
└─────────────┘  │  ┌──────▼──────┐ │  │  (PDF + Word)       │
                 │  │    Juez     │ │  └─────────────────────┘
                 │  └─────────────┘ │
                 └──────────────────┘
       │                  │
┌──────▼──────┐  ┌────────▼────────┐
│    MySQL    │  │    ChromaDB      │
│  (metadata  │  │  (vectores RAG)  │
│   + logs)   │  └──────────────────┘
└─────────────┘
```

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Frontend | Vue.js 3 (Composition API) + Vite + Tailwind CSS |
| Backend | Python 3.11 · FastAPI · Uvicorn |
| IA SDK | **Google GenAI SDK** (`google-genai`) — sin LangChain |
| Modelos | Gemini 2.0 Flash · Gemini 2.0 Flash Exp · text-embedding-004 |
| Vector DB | ChromaDB (persistente) |
| Base de datos | MySQL 8.0 (SQLAlchemy async) |
| MCP | Model Context Protocol — servidor ICR propio |
| Reportes | fpdf2 (PDF) · python-docx (Word) |

---

## Estructura del Proyecto

```
examgrader/
├── backend/
│   ├── main.py                  # FastAPI app + todos los endpoints
│   ├── config.py                # Settings (pydantic-settings)
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   ├── db/
│   │   ├── database.py          # ORM SQLAlchemy + AsyncSession
│   │   └── schema.sql           # Esquema MySQL completo
│   ├── agents/
│   │   └── consensus.py         # 3 agentes: CalificadorA + B + Juez
│   ├── services/
│   │   ├── icr_service.py       # Extracción de texto con Gemini Vision
│   │   ├── rag_service.py       # ChromaDB + Google Embeddings
│   │   └── report_service.py    # Generación PDF y Word
│   └── mcp_servers/
│       └── icr_server.py        # Servidor MCP para ICR
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue              # Layout + navegación
│   │   ├── router/index.js
│   │   ├── stores/appStore.js   # Pinia store
│   │   ├── composables/useApi.js # Axios API client
│   │   ├── style.css            # Tailwind + componentes globales
│   │   └── views/
│   │       ├── HomeView.vue     # Dashboard / Landing
│   │       ├── GradeView.vue    # Upload + slider de exigencia
│   │       ├── ExamDetailView.vue # Comparación de agentes
│   │       ├── HistoryView.vue  # Historial paginado
│   │       ├── MaterialsView.vue # Gestión RAG
│   │       └── ConfigView.vue   # Configuración del sistema
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── vite.config.js
│   └── tailwind.config.js
└── docker-compose.yml
```

---

## Esquema de Base de Datos (MySQL)

```
docentes ──────────── materiales_curso
    │                       │
    └──── examenes ──────────┘
              │
    ┌─────────┼──────────┐
    │         │          │
preguntas  calificaciones  logs_consenso
extraidas   _finales      (agente A/B/Juez)
```

**Tablas principales:**
- `examenes` — metadata, imágenes, estado, punteos
- `preguntas_extraidas` — cada pregunta/respuesta del examen
- `calificaciones_finales` — resultado del Juez + rutas PDF/Word
- `logs_consenso` — auditoría completa: prompt, respuesta JSON, tokens, latencia

---

## Flujo de Procesamiento

```
[Imágenes] → ICR (MCP/Gemini Vision)
                 ↓
          [Texto + YAML estructurado]
                 ↓
         RAG Query → ChromaDB
                 ↓
        [Contexto del curso]
                 ↓
    ┌────────────┴────────────┐
    ▼                         ▼
Calificador A           Calificador B
(gemini-2.0-flash)  (gemini-2.0-flash-exp)
    │                         │
    └────────────┬────────────┘
                 ▼
           Agente Juez
        (consenso + justificación)
                 ▼
       Reporte PDF + Word
```

---

## Configuración e Instalación

### 1. Requisitos previos

- Python 3.11+
- Node.js 20+
- MySQL 8.0+
- API Key de Google AI Studio: https://aistudio.google.com

### 2. Backend

```bash
cd backend
cp .env.example .env
# Editar .env con tu GEMINI_API_KEY y credenciales MySQL

pip install -r requirements.txt

# Crear tablas (automático al arrancar la API, o manual):
mysql -u root -p < db/schema.sql

uvicorn main:app --reload --port 8000
```

### 3. MCP Server ICR (en terminal separada)

```bash
cd backend
GEMINI_API_KEY=your_key python mcp_servers/icr_server.py
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

### 5. Docker Compose (recomendado para producción)

```bash
# Crear .env en la raíz del proyecto
echo "GEMINI_API_KEY=your_key_here" > .env

docker-compose up -d
# Frontend: http://localhost:80
# API Docs: http://localhost:8000/api/docs
```

---

## API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET`  | `/api/health` | Estado del sistema |
| `POST` | `/api/upload` | Subir imágenes de examen |
| `POST` | `/api/process/{id}` | Iniciar procesamiento (ICR+RAG+Agentes) |
| `GET`  | `/api/history` | Historial paginado |
| `GET`  | `/api/history/{id}` | Detalle con comparación de agentes |
| `GET`  | `/api/config-exigencia` | Configuración actual |
| `POST` | `/api/config-exigencia` | Actualizar nivel 1-10 |
| `POST` | `/api/materials/upload` | Indexar PDF en ChromaDB |
| `GET`  | `/api/materials` | Listar materiales indexados |
| `GET`  | `/api/download/pdf/{id}` | Descargar reporte PDF |
| `GET`  | `/api/download/word/{id}` | Descargar reporte Word |

Documentación interactiva: **http://localhost:8000/api/docs**

---

## Nivel de Exigencia

| Nivel | Modo | Descripción |
|-------|------|-------------|
| 1-2 | 😊 Amigo | Valora el esfuerzo, tolera errores menores |
| 3-4 | 🙂 Comprensivo | Crédito parcial por procedimientos |
| 5-6 | ⚖️ Balanceado | Evalúa proceso y resultado objetivamente |
| 7-8 | 🎯 Estricto | Penaliza errores de signos y procedimientos incompletos |
| 9-10 | 🔬 Experto | Solo puntaje completo si todo es correcto |

---

## Soporte LaTeX

El sistema detecta y procesa expresiones matemáticas en los exámenes:

| Expresión | LaTeX generado |
|-----------|---------------|
| Fracción | `$\frac{a}{b}$` |
| Raíz cuadrada | `$\sqrt{x}$` |
| Potencia | `$x^{n}$` |
| Subíndice | `$x_{i}$` |
| Producto notable | `$(a+b)^2 = a^2 + 2ab + b^2$` |
| Ecuación display | `$$E = mc^2$$` |

---

## Variables de Entorno

```env
# Google GenAI (requerido)
GEMINI_API_KEY=AIza...

# MySQL
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=edugrade_ai

# ChromaDB
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION=materiales_curso

# Modelos IA
MODEL_CALIFICADOR_A=gemini-2.0-flash
MODEL_CALIFICADOR_B=gemini-2.0-flash-exp
MODEL_JUEZ=gemini-2.0-flash
MODEL_EMBEDDING=models/text-embedding-004
MODEL_ICR=gemini-2.0-flash
```

---

## Tecnologías Clave

- **Google GenAI SDK** (`google.genai`) — llamadas directas sin LangChain
- **MCP** (Model Context Protocol) — servidor ICR como herramienta estándar
- **ChromaDB** — almacenamiento vectorial persistente con búsqueda coseno
- **SQLAlchemy async** — ORM asíncrono sobre aiomysql
- **Vue 3 Composition API** + **Pinia** — estado reactivo y composables
- **Tailwind CSS v3** — estilos utilitarios sin build custom

---

*EduGrade AI — Proyecto Académico · Sistema Inteligente Multimodal*
