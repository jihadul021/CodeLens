import httpx
import os

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_KEY = os.environ["GROQ_API_KEY"]
GROQ_MODEL = "openai/gpt-oss-120b"  # fast, strong general-purpose model on Groq

async def generate_answer(question: str, chunks: list) -> dict:
    context = "\n\n".join(
        f"# {c.file_path}\n{c.content}" for c in chunks
    )

    prompt = f"""You are answering questions about a codebase using only the code below.
Cite the file path(s) you used in your answer.

CODE CONTEXT:
{context}

QUESTION: {question}

Answer concisely, referencing specific files/functions where relevant."""

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
        "sources": [c.file_path for c in chunks],
    }