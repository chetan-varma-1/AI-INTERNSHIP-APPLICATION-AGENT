# AI Internship Agent

AI-powered internship matching platform. Users sign up, upload a resume, and get
matched against scraped internship listings using a RAG pipeline.

## Implemented project structure

```text
AI Internship Agent/
├── app/
│   ├── main.py                         # FastAPI entry point
│   ├── api/
│   │   ├── auth.py                     # Signup, login, logout, refresh, /me
│   │   ├── jobs.py                     # Authenticated scrape + list jobs
│   │   ├── matching.py                 # Authenticated internship matching
│   │   └── user_details.py             # Resume / cover letter / profile summary
│   ├── auth/                           # JWT, cookies, password, dependencies
│   ├── agents/                         # Matching orchestrator + agents
│   ├── services/
│   │   ├── job_scrape_service.py       # Parallel Postgres + RAG persist
│   │   ├── profile_service.py
│   │   └── user_detail_service.py
│   ├── database/
│   │   ├── connection.py
│   │   └── repositories/
│   ├── models/                         # User, UserDetail, Job
│   ├── rag/                            # Embeddings, Chroma, ingestion, retrieval
│   ├── schemas/
│   ├── scraper/
│   │   └── mocker_scraper.py           # Mock internship data source
│   └── llm/
├── migrations/
│   └── versions/
│       ├── 20260730_0001_initial_schema.py
│       └── 20260805_0002_create_jobs_table.py
├── tests/
├── docker-compose.yml                  # Chroma HTTP server
├── .env.example
├── alembic.ini
├── pyproject.toml
└── README.md
```

## Authentication policy

JWT access and refresh tokens are stored in **HTTP-only cookies**.

| Kind | Endpoints |
| --- | --- |
| Public | `GET /health`, `POST /auth/signup`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `/docs` |
| Protected | every other business endpoint (requires a valid access-token cookie) |

New endpoints must use `get_current_user` (router-level dependency preferred).
Clients do **not** send a `user_id`; ownership comes from the verified cookie.

## API overview

### Auth

| Method | Path | Auth |
| --- | --- | --- |
| `POST` | `/auth/signup` | No |
| `POST` | `/auth/login` | No |
| `POST` | `/auth/refresh` | Refresh cookie |
| `POST` | `/auth/logout` | No |
| `GET` | `/auth/me` | Access cookie |

### Jobs (scrape + list)

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| `POST` | `/jobs/scrape?reset_vectors=true` | Required | Runs mock scraper, then concurrently writes to Postgres `jobs` and RAG/Chroma |
| `GET` | `/jobs` | Required | Lists jobs from PostgreSQL |

Each scrape **replaces** existing Postgres rows and (by default) resets the Chroma collection before re-indexing.

### User documents

| Method | Path | Auth |
| --- | --- | --- |
| `POST` | `/resumes/parse` | Required |
| `GET` | `/resumes` | Required |
| `POST` | `/cover-letters/parse` | Required |
| `GET` | `/cover-letters` | Required |
| `POST` | `/profile-summary` | Required |

### Matching

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| `POST` | `/matching` | Required | Multipart: either `user_detail_id` **or** a new PDF/DOCX `file`, not both |

Skills used for matching = signup profile skills **merged with** resume skills.

Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Setup

```powershell
uv sync
copy .env.example .env
```

Edit `.env` with your PostgreSQL password and secrets.

### PostgreSQL

Start the local Postgres service, then apply migrations:

```powershell
uv run alembic upgrade head
```

If the database was created earlier via app startup `create_all`, mark the baseline as applied:

```powershell
uv run alembic stamp head
```

### ChromaDB (vector store)

| Mode | Storage | Notes |
| --- | --- | --- |
| `http` (default) | Standalone Chroma server | Preferred for browsing with a GUI |
| `embedded` | Local `vector_db/` | No external server |

```powershell
docker compose up -d
curl http://localhost:6333/api/v2/heartbeat
```

```ini
CHROMA_MODE=http
CHROMA_HOST=localhost
CHROMA_PORT=6333
```

### Ollama

```powershell
ollama pull mxbai-embed-large
ollama pull llama3.2:1b
```

Optional one-off RAG ingestion (also covered by `POST /jobs/scrape`):

```powershell
uv run python -m app.rag.ingestion
```

## Run the application

```powershell
uv run python -m uvicorn app.main:app --reload
```

Typical flow in `/docs`:

1. `POST /auth/signup` or `POST /auth/login` (cookies are set automatically)
2. `POST /jobs/scrape` to load jobs into Postgres + Chroma
3. `GET /jobs` to inspect stored jobs
4. Upload a resume / run `POST /matching`

## Run the tests

```powershell
uv run pytest
```
