"use client";

import { useState, useRef } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

function parseGithubUrl(url: string): { owner: string; repo: string } | null {
  try {
    const cleaned = url.trim().replace(/\/$/, "").replace(/\.git$/, "");
    const parts = new URL(cleaned).pathname.split("/").filter(Boolean);
    if (parts.length < 2) return null;
    return { owner: parts[0], repo: parts[1] };
  } catch {
    return null;
  }
}

export default function Home() {
  const [repoUrl, setRepoUrl] = useState("");
  const [status, setStatus] = useState<string>("idle");
  const [log, setLog] = useState<string>("");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function pollStatus(owner: string, repo: string) {
    // clear any previous poller before starting a new one
    if (pollRef.current) clearInterval(pollRef.current);

    pollRef.current = setInterval(async () => {
      const res = await fetch(`${API_URL}/github/status?owner=${owner}&repo=${repo}`);
      if (!res.ok) {
        // 404 = row not created yet, keep polling
        return;
      }
      const data = await res.json();
      console.log("status:", data);
      setLog(JSON.stringify(data, null, 2));

      if (data.status === "done" || data.status === "failed") {
        if (pollRef.current) clearInterval(pollRef.current);
        setStatus(data.status);
      }
    }, 2000);
  }

  async function handleIngest() {
    const parsed = parseGithubUrl(repoUrl);
    if (!parsed) {
      setLog("Invalid GitHub URL");
      return;
    }

    setStatus("starting");
    setLog("Starting ingestion...");

    const res = await fetch(`${API_URL}/github/ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: repoUrl.trim() }),
    });
    const data = await res.json();
    console.log("ingest response:", data);
    setStatus("indexing");

    pollStatus(parsed.owner, parsed.repo);
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-4 p-8">
      <h1 className="text-2xl font-bold">CodeLens</h1>
      <div className="flex gap-2 w-full max-w-xl">
        <input
          className="flex-1 border rounded px-3 py-2"
          placeholder="https://github.com/owner/repo"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
        />
        <button
          className="bg-black text-white px-4 py-2 rounded"
          onClick={handleIngest}
        >
          Ingest
        </button>
      </div>
      <p className="text-sm text-gray-500">Status: {status}</p>
      <pre className="text-xs bg-gray-100 p-4 rounded w-full max-w-xl overflow-auto">
        {log}
      </pre>
    </main>
  );
}