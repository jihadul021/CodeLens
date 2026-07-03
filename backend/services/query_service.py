from sqlalchemy import select
from models import CodeChunk, Repo
from services.embedding_service import get_embeddings_batch

async def search_chunks(db, repo_id: int, question: str, top_k: int = 8):
    [query_embedding] = await get_embeddings_batch([question])

    result = await db.execute(
        select(CodeChunk)
        .where(CodeChunk.repo_id == repo_id)
        .order_by(CodeChunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )
    return result.scalars().all()