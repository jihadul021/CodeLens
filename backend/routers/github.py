from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from services.github_service import parse_github_url, fetch_repo_files
from services.ingestion_service import ingest_repo
from database import get_db

router = APIRouter(prefix="/github", tags=["GitHub"])

class RepoRequest(BaseModel):
    url: str

@router.post("/ingest")
async def ingest_repository(
    request: RepoRequest,
    background_tasks: BackgroundTasks,
):
    try:
        owner, repo_name = parse_github_url(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    background_tasks.add_task(ingest_repo, request.url)  # no db here

    return {
        "message": "Ingestion started",
        "owner": owner,
        "repo": repo_name,
        "status": "indexing",
    }

@router.get("/status")
async def get_repo_status(
    owner: str,
    repo: str,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from models import Repo

    result = await db.execute(
        select(Repo)
        .where(Repo.owner == owner, Repo.repo == repo)
        .order_by(Repo.id.desc())  # get the latest one
        .limit(1)
    )
    repo_record = result.scalar_one_or_none()

    if not repo_record:
        raise HTTPException(status_code=404, detail="Repo not indexed yet")

    return {
        "owner": owner,
        "repo": repo,
        "status": repo_record.status,
        "total_files": repo_record.total_files,
    }