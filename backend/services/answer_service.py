import httpx
import os
import json

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_KEY = os.environ["GROQ_API_KEY"]
GROQ_MODEL = "openai/gpt-oss-120b"  # fast, strong general-purpose model on Groq


def build_prompt(question: str, chunks: list) -> str:
    context = "\n\n".join(
        f"# {c.file_path}\n{c.content}" for c in chunks
    )

    return f"""You are answering questions about a codebase using only the code below.
Cite the file path(s) you used in your answer.

CODE CONTEXT:
{context}

QUESTION: {question}

Answer concisely, referencing specific files/functions where relevant."""


def dedupe_sources(chunks: list) -> list[dict]:
    seen = {}
    for c in chunks:
        if c.file_path not in seen:
            seen[c.file_path] = {
                "file": c.file_path,
                "start_line": getattr(c, "start_line", None),
                "end_line": getattr(c, "end_line", None),
            }
    return list(seen.values())


async def generate_answer(question: str, chunks: list) -> dict:
    """Non-streaming: waits for full response, returns JSON."""
    prompt = build_prompt(question, chunks)

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            },
        )
        response.raise_for_status()
        data = response.json()
        answer_text = data["choices"][0]["message"]["content"]

    return {
        "answer": answer_text,
        "sources": dedupe_sources(chunks),
    }


async def stream_answer(question: str, chunks: list):
    """Streaming: yields SSE events as Groq generates the answer, token by token."""
    prompt = build_prompt(question, chunks)

    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream(
            "POST",
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "stream": True,
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                payload = line[6:]
                if payload == "[DONE]":
                    break
                data = json.loads(payload)
                delta = data["choices"][0]["delta"].get("content", "")
                if delta:
                    yield f"data: {json.dumps({'text': delta})}\n\n"

    # after the full answer streams, send sources as a final event
    yield f"data: {json.dumps({'sources': dedupe_sources(chunks)})}\n\n"
    yield "data: [DONE]\n\n"