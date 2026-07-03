import os
import httpx
from dotenv import load_dotenv

load_dotenv()

JINA_API_KEY = os.getenv("JINA_API_KEY")
JINA_URL = "https://api.jina.ai/v1/embeddings"
HEADERS = {
    "Authorization": f"Bearer {JINA_API_KEY}",
    "Content-Type": "application/json",
}

async def get_embedding(text: str) -> list[float]:
    """Embed a code chunk using Jina's code embedding model."""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            JINA_URL,
            headers=HEADERS,
            json={
                "model": "jina-embeddings-v2-base-code",
                "input": [text],
            }
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]

async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Embed multiple chunks in one API call instead of one by one."""
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            JINA_URL,
            headers=HEADERS,
            json={
                "model": "jina-embeddings-v2-base-code",
                "input": texts,
            }
        )
        response.raise_for_status()
        data = response.json()["data"]
        # sort by index to maintain order
        data.sort(key=lambda x: x["index"])
        return [item["embedding"] for item in data]


async def get_query_embedding(text: str) -> list[float]:
    """Embed a user question."""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            JINA_URL,
            headers=HEADERS,
            json={
                "model": "jina-embeddings-v2-base-code",
                "input": [text],
            }
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]