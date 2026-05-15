
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routers import github

load_dotenv()

app = FastAPI(
    title="RepoMind API",
    description="Ask questions about any GitHub codebase using RAG",
    version="0.1.0",
)

# CORS: allows your Next.js frontend (localhost:3000) to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(github.router)


@app.get("/health")
async def health_check():
    """Simple endpoint to confirm the server is running."""
    return {"status": "ok", "service": "RepoMind API"}