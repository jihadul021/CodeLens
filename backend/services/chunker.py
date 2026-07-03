def chunk_code(content: str, file_path: str, chunk_size: int = 40, overlap: int = 5) -> list[str]:
    """
    Split a file's content into overlapping chunks of lines.
    
    chunk_size=40 means each chunk is 40 lines.
    overlap=5 means consecutive chunks share 5 lines.
    
    Overlap is important — if a concept spans a chunk boundary,
    the overlap ensures it's fully captured in at least one chunk.
    """
    lines = content.split("\n")
    chunks = []
    start = 0

    while start < len(lines):
        end = start + chunk_size
        chunk_lines = lines[start:end]
        chunk_text = "\n".join(chunk_lines).strip()

        if chunk_text:  # skip empty chunks
            # Prepend file path so the LLM knows where this code lives
            chunks.append(f"File: {file_path}\n\n{chunk_text}")

        start += chunk_size - overlap  # move forward with overlap

    return chunks