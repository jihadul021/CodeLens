from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.github_service import parse_github_url, fetch_repo_files

router = APIRouter(prefix="/github", tags=["GitHub"])


class RepoRequest(BaseModel):
    url: str
 

class FileInfo(BaseModel):
    path: str
    size: int


class RepoResponse(BaseModel):
    owner: str
    repo: str
    total_files: int
    files: list[FileInfo]


@router.post("/fetch", response_model=RepoResponse)
async def fetch_repository(request: RepoRequest):
    try:
        owner, repo = parse_github_url(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        files = await fetch_repo_files(owner, repo)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return RepoResponse(
        owner=owner,
        repo=repo,
        total_files=len(files),
        files=[FileInfo(path=f["path"], size=f["size"]) for f in files],
    )