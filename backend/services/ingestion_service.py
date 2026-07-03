import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Repo, CodeChunk
from services.github_service import parse_github_url, fetch_repo_files
from services.embedding_service import get_embedding, get_embeddings_batch
from services.chunker import chunk_code
from database import AsyncSessionLocal  # import this instead

async def ingest_repo(url: str) -> None:
    print(f"🚀 Starting ingestion for {url}")  # add this
    async with AsyncSessionLocal() as db:
        owner, repo_name = parse_github_url(url)
        print(f"📁 Parsed: {owner}/{repo_name}")  # add this

        result = await db.execute(
            select(Repo)
            .where(Repo.owner == owner, Repo.repo == repo_name)
            .order_by(Repo.id.desc())
            .limit(1)
        )
        existing = result.scalar_one_or_none()
        if existing and existing.status in ("done", "indexing"):
            print("⏭️ Already indexed, skipping")  # add this
            return

        repo = Repo(owner=owner, repo=repo_name, status="indexing")
        db.add(repo)
        await db.commit()
        await db.refresh(repo)
        print(f"💾 Repo record created with id={repo.id}")  # add this

        try:
            print("📡 Fetching files from GitHub...")  # add this
            files = await fetch_repo_files(owner, repo_name)
            print(f"📄 Got {len(files)} files")  # add this
            total_chunks = 0

            for file in files:
                print(f"⚙️ Processing {file['path']}")
                chunks = chunk_code(file["content"], file["path"])
                
                if not chunks:
                    continue

                # One API call for all chunks in this file
                embeddings = await get_embeddings_batch(chunks)

                for chunk_text, embedding in zip(chunks, embeddings):
                    chunk = CodeChunk(
                        repo_id=repo.id,
                        file_path=file["path"],
                        content=chunk_text,
                        embedding=embedding,
                    )
                    db.add(chunk)
                    total_chunks += 1

                await db.commit()

            repo.status = "done"
            repo.total_files = len(files)
            await db.commit()
            print(f"✅ Done: {len(files)} files, {total_chunks} chunks")

        except Exception as e:
            import traceback
            print(f"❌ Ingestion failed: {e}")
            traceback.print_exc()  # prints full error stack
            repo.status = "failed"
            await db.commit()
            raise e