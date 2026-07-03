# main.py or routes/query.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from database import get_db
from services.query_service import search_chunks
from models import Repo
from sqlalchemy import select
from services.github_service import parse_github_url
from fastapi.responses import StreamingResponse
from services.answer_service import generate_answer, stream_answer

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

# @router.get("/repos/{owner}/{repo_name}/status")
# async def get_repo_status(owner: str, repo_name: str, db=Depends(get_db)):
#     result = await db.execute(
#         select(Repo)
#         .where(Repo.owner == owner, Repo.repo == repo_name)
#         .order_by(Repo.id.desc())
#         .limit(1)
#     )
#     repo = result.scalar_one_or_none()
#     if not repo:
#         return {"status": "not_found"}
#     return {
#         "status": repo.status,
#         "total_files": repo.total_files,
#     }

@router.post("/query/stream")
async def query_repo_stream(req: QueryRequest, db=Depends(get_db)):
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

    return StreamingResponse(stream_answer(req.question, chunks), media_type="text/event-stream")