# main.py or routes/query.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from database import get_db
from services.query_service import search_chunks
from services.answer_service import generate_answer
from models import Repo
from sqlalchemy import select
from services.github_service import parse_github_url

router = APIRouter()

class QueryRequest(BaseModel):
    repo_url: str
    question: str

@router.post("/query")
async def query_repo(req: QueryRequest, db=Depends(get_db)):
    owner, repo_name = parse_github_url(req.repo_url)

    result = await db.execute(
        select(Repo)
        .where(Repo.owner == owner, Repo.repo == repo_name, Repo.status == "done")
        .order_by(Repo.id.desc())
        .limit(1)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        return {"error": "Repo not indexed yet"}

    chunks = await search_chunks(db, repo.id, req.question)
    if not chunks:
        return {"error": "No relevant code found"}

    return await generate_answer(req.question, chunks)