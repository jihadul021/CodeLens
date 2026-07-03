def chunk_code(content: str, file_path: str, chunk_size: int = 40, overlap: int = 5) -> list[dict]:
    lines = content.split("\n")
    chunks = []
    start = 0

    while start < len(lines):
        end = start + chunk_size
        chunk_lines = lines[start:end]
        chunk_text = "\n".join(chunk_lines).strip()

        if chunk_text:
            chunks.append({
                "text": f"File: {file_path}\n\n{chunk_text}",
                "start_line": start + 1,   # 1-indexed for GitHub URLs
                "end_line": min(end, len(lines)),
            })

        start += chunk_size - overlap

    return chunks