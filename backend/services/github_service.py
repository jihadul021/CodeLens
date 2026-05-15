import httpx
import os
from typing import Optional

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".java", ".go", ".rb", ".rs", ".cpp",
    ".c", ".h", ".cs", ".php", ".swift",
    ".md", ".yaml", ".yml", ".toml", ".json",
    ".html", ".css", ".sh", ".env.example",
}

EXCLUDED_PATHS = {
    "node_modules", ".git", "__pycache__",
    "dist", "build", ".next", "venv",
}


def parse_github_url(url: str) -> tuple[str, str]:

    url = url.rstrip("/").replace("https://github.com/", "")
    parts = url.split("/")
    if len(parts) < 2:
        raise ValueError("Invalid GitHub URL. Expected: https://github.com/owner/repo")
    return parts[0], parts[1]


async def fetch_repo_files(owner: str, repo: str, path: str = "") -> list[dict]:
    """
    Recursively fetches all code files from a GitHub repo using the Contents API.
    Returns a list of dicts with 'path' and 'content'.
    """
    token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"

    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(url, headers=headers)

        if response.status_code == 404:
            raise ValueError(f"Repository '{owner}/{repo}' not found or is private.")
        if response.status_code != 200:
            raise Exception(f"GitHub API error: {response.status_code} - {response.text}")

        items = response.json()

    if isinstance(items, dict):
        items = [items]

    files = []

    for item in items:
        # Skip excluded folders
        if any(excluded in item["path"] for excluded in EXCLUDED_PATHS):
            continue

        if item["type"] == "dir":
            # Recurse into subdirectory
            sub_files = await fetch_repo_files(owner, repo, item["path"])
            files.extend(sub_files)

        elif item["type"] == "file":
            ext = "." + item["name"].split(".")[-1] if "." in item["name"] else ""
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            # Skip files larger than 100KB 
            if item.get("size", 0) > 100_000:
                continue

            # Fetch the actual file content
            file_content = await fetch_file_content(item["download_url"], headers)
            if file_content:
                files.append({
                    "path": item["path"],
                    "content": file_content,
                    "size": item.get("size", 0),
                })

    return files


async def fetch_file_content(download_url: str, headers: dict) -> Optional[str]:
    # Downloads raw file content from a URL.
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(download_url, headers=headers)
        if response.status_code != 200:
            return None
        try:
            return response.text  # Decode as UTF-8 text
        except Exception:
            return None  # Binary files get skipped