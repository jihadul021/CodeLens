# CodeLens

## Live Demo: https://code-lens-beta.vercel.app/

Ask any public GitHub repository a question in natural language and get a streamed, source-cited answer — pointing straight back to the exact file and line range the answer came from.

CodeLens ingests a repo, chunks and embeds its source code, and uses retrieval-augmented generation (RAG) to answer natural-language questions grounded in the actual codebase — not a general-purpose LLM guess.

## How it works

1. **Ingest** — paste a public GitHub repo URL. CodeLens fetches every file, splits it into chunks, and embeds each chunk into a vector using Jina's code embedding model.
2. **Store** — embeddings are stored in PostgreSQL with `pgvector`, alongside the file path and line range each chunk came from.
3. **Ask** — ask a question about the repo. CodeLens embeds the question, runs a similarity search against the stored chunks, and retrieves the most relevant pieces of code.
4. **Answer** — those chunks are passed to an LLM (via Groq) which generates an answer, streamed back token-by-token, along with a ranked list of the exact source files (and line ranges) the answer is grounded in.

## Tech stack

**Backend**
- FastAPI (async)
- PostgreSQL + `pgvector` for similarity search
- SQLAlchemy (async ORM)
- Jina Embeddings API (code embedding model)
- Groq API for LLM generation
- Server-Sent Events (SSE) for streaming responses

**Frontend**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS v4
- Manual SSE stream parsing (`ReadableStream`) for real-time token rendering

## Features

- 🔍 Ask questions about any public GitHub repo — no setup on the repo's end required
- ⚡ Streamed, token-by-token answers (no waiting for the full response)
- 📎 Every answer is cited with the exact file and line range it came from, linked directly to GitHub
- 🚀 Batched embedding pipeline — one API call per file instead of per chunk, for fast ingestion
- 🔄 Background ingestion with live status polling — no blocking requests

## Getting started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL with the `pgvector` extension enabled
- API keys for [Jina AI](https://jina.ai) (embeddings) and [Groq](https://groq.com) (LLM inference)

### Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in `backend/`:

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost/codelens
JINA_API_KEY=your_jina_api_key
GROQ_API_KEY=your_groq_api_key
```

Run the server:

```bash
uvicorn main:app --reload
```

### Frontend setup

```bash
cd frontend
npm install
```

Create a `.env.local` file in `frontend/`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Run the dev server:

```bash
npm run dev
```

Visit `http://localhost:3000`.

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/github/ingest` | Starts background ingestion for a given repo URL |
| `GET` | `/github/status?owner=&repo=` | Returns ingestion status (`indexing`, `done`, `failed`) and file count |
| `POST` | `/query` | Returns a full (non-streaming) answer with sources |
| `POST` | `/query/stream` | Streams the answer via SSE, followed by a `sources` event |

## Project structure

```
codelens/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── routers/
│   │   ├── github.py       # ingestion + status endpoints
│   │   └── query.py        # query + streaming endpoints
│   └── services/
│       ├── github_service.py     # GitHub API + URL parsing
│       ├── ingestion_service.py  # chunking + embedding pipeline
│       ├── embedding_service.py 
│       ├── chunker.py            # code chunking with line tracking
│       ├── query_service.py      # vector similarity search
│       └── answer_service.py   
└── frontend/
    └── app/
        └── page.tsx        
```
