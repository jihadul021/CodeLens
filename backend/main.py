from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routers import github
from database import init_db
from routers.query import router as query_router

load_dotenv()

app = FastAPI(
    title="CodeLens API",
    description="Ask questions about any GitHub codebase using RAG",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",         
        "https://code-lens-beta.vercel.app",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(github.router)
app.include_router(query_router)

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "CodeLens API"}
