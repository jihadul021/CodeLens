"use client";

import { useState, useRef } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

interface Source {
  file: string;
  start_line: number | null;
  end_line: number | null;
}

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

function sourceUrl(owner: string, repo: string, s: Source): string {
  const base = `https://github.com/${owner}/${repo}/blob/main/${s.file}`;
  if (s.start_line == null) return base;
  return s.end_line && s.end_line !== s.start_line
    ? `${base}#L${s.start_line}-L${s.end_line}`
    : `${base}#L${s.start_line}`;
}

const STATUS_STYLES: Record<
  string,
  { dot: string; text: string; label: string }
> = {
  idle: { dot: "bg-zinc-600", text: "text-zinc-500", label: "waiting for a repo" },
  starting: { dot: "bg-amber-500 animate-pulse", text: "text-amber-400", label: "starting…" },
  indexing: { dot: "bg-amber-500 animate-pulse", text: "text-amber-400", label: "indexing…" },
  done: { dot: "bg-emerald-500", text: "text-emerald-400", label: "indexed" },
  failed: { dot: "bg-red-500", text: "text-red-400", label: "ingestion failed" },
};

export default function Home() {
  const [repoUrl, setRepoUrl] = useState("");
  const [status, setStatus] = useState<string>("idle");
  const [totalFiles, setTotalFiles] = useState<number | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<Source[]>([]);
  const [asking, setAsking] = useState(false);

  const parsed = parseGithubUrl(repoUrl);
  const s = STATUS_STYLES[status] ?? STATUS_STYLES.idle;

  function pollStatus(owner: string, repo: string) {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      const res = await fetch(`${API_URL}/github/status?owner=${owner}&repo=${repo}`);
      if (!res.ok) return;
      const data = await res.json();
      setTotalFiles(data.total_files ?? null);
      if (data.status === "done" || data.status === "failed") {
        if (pollRef.current) clearInterval(pollRef.current);
        setStatus(data.status);
      }
    }, 2000);
  }

  async function handleIngest() {
    if (!parsed) return;
    setStatus("starting");
    setTotalFiles(null);
    setAnswer("");
    setSources([]);

    const res = await fetch(`${API_URL}/github/ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: repoUrl.trim() }),
    });
    await res.json();
    setStatus("indexing");
    pollStatus(parsed.owner, parsed.repo);
  }

  async function handleAsk() {
    if (!parsed || status !== "done" || !question.trim()) return;

    setAsking(true);
    setAnswer("");
    setSources([]);

    const res = await fetch(`${API_URL}/query/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo_url: repoUrl.trim(), question: question.trim() }),
    });

    if (!res.body) {
      setAsking(false);
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() || "";

      for (const event of events) {
        const line = event.trim();
        if (!line.startsWith("data:")) continue;
        const payload = line.slice(5).trim();
        if (payload === "[DONE]") continue;

        try {
          const parsedPayload = JSON.parse(payload);
          if (parsedPayload.text) {
            setAnswer((prev) => prev + parsedPayload.text);
          } else if (parsedPayload.sources) {
            setSources(parsedPayload.sources);
          }
        } catch (e) {
          console.error("Failed to parse SSE payload:", payload, e);
        }
      }
    }

    setAsking(false);
  }

  return (
    <main className="min-h-screen flex justify-center px-4 py-10 sm:py-16">
      <div className="w-full max-w-2xl flex flex-col gap-6">
        {/* Terminal-style title bar */}
        <div className="rounded-t-lg border border-zinc-800 bg-[#0F131C] px-4 py-3 flex items-center gap-2">
          <div className="flex gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500/70" />
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500/70" />
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/70" />
          </div>
          <span className="ml-2 text-xs font-mono text-zinc-500">
            {parsed ? `${parsed.owner}/${parsed.repo}` : "codelens"}
          </span>
        </div>

        {/* Main panel */}
        <div className="border border-t-0 border-zinc-800 bg-[#0F131C] rounded-b-lg p-6 sm:p-8 flex flex-col gap-6 -mt-6">
          <div>
            <h1 className="font-mono text-xl font-semibold tracking-tight text-zinc-100">
              CodeLens
            </h1>
            <p className="text-sm text-zinc-500 mt-1">
              Point it at a public GitHub repo. Ask it anything about the code.
            </p>
          </div>

          {/* Repo input */}
          <div className="flex flex-col gap-2">
            <div className="flex flex-col sm:flex-row gap-2">
              <input
                className="flex-1 rounded-md border border-zinc-700 bg-[#0B0E14] px-3 py-2.5 font-mono text-sm text-zinc-200 placeholder:text-zinc-600 outline-none focus:border-emerald-600 focus:ring-1 focus:ring-emerald-600 transition-colors"
                placeholder="github.com/owner/repo"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleIngest()}
              />
              <button
                className="rounded-md bg-emerald-600 hover:bg-emerald-500 disabled:bg-zinc-700 disabled:text-zinc-500 text-[#0B0E14] font-mono text-sm font-semibold px-4 py-2.5 transition-colors"
                onClick={handleIngest}
                disabled={!parsed || status === "starting" || status === "indexing"}
              >
                Index repo
              </button>
            </div>

            <div className="flex items-center gap-2 pl-1">
              <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
              <span className={`text-xs font-mono ${s.text}`}>{s.label}</span>
              {totalFiles != null && status === "done" && (
                <span className="text-xs font-mono text-zinc-600">
                  · {totalFiles} files
                </span>
              )}
            </div>
          </div>

          {/* Q&A section */}
          {status === "done" && parsed && (
            <div className="flex flex-col gap-4 border-t border-zinc-800 pt-6">
              <div className="flex flex-col sm:flex-row gap-2">
                <input
                  className="flex-1 rounded-md border border-zinc-700 bg-[#0B0E14] px-3 py-2.5 text-sm text-zinc-200 placeholder:text-zinc-600 outline-none focus:border-emerald-600 focus:ring-1 focus:ring-emerald-600 transition-colors"
                  placeholder="Where's the authentication logic?"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAsk()}
                />
                <button
                  className="rounded-md bg-zinc-100 hover:bg-white disabled:bg-zinc-700 disabled:text-zinc-500 text-[#0B0E14] font-mono text-sm font-semibold px-4 py-2.5 transition-colors"
                  onClick={handleAsk}
                  disabled={asking || !question.trim()}
                >
                  {asking ? "Thinking…" : "Ask"}
                </button>
              </div>

              {(answer || asking) && (
                <div className="rounded-md border border-zinc-800 bg-[#0B0E14] overflow-hidden">
                  <div className="flex items-center gap-2 border-b border-zinc-800 px-3 py-1.5">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-600">
                      answer
                    </span>
                  </div>
                  <div className="px-4 py-3 font-mono text-sm leading-relaxed text-zinc-300 whitespace-pre-wrap">
                    {answer}
                    {asking && (
                      <span className="inline-block w-2 h-4 bg-emerald-500 ml-0.5 animate-pulse align-middle" />
                    )}
                  </div>
                </div>
              )}

              {sources.length > 0 && (
                <div className="flex flex-col gap-1.5">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-600">
                    sources · ranked by relevance
                  </span>
                  <div className="flex flex-col divide-y divide-zinc-800 rounded-md border border-zinc-800 overflow-hidden">
                    {sources.map((src, i) => (
                      
                      <a
                        href={sourceUrl(parsed.owner, parsed.repo, src)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="group flex items-center gap-3 px-3 py-2 bg-[#0B0E14] hover:bg-[#131722] transition-colors"
                      >
                        <span className="text-xs font-mono text-zinc-600 tabular-nums w-6 shrink-0">
                          {String(i + 1).padStart(2, "0")}
                        </span>
                        <span className="text-xs font-mono text-zinc-300 group-hover:text-emerald-400 transition-colors truncate">
                          {src.file}
                        </span>
                        {src.start_line != null && (
                          <span className="text-xs font-mono text-zinc-600 ml-auto shrink-0">
                            L{src.start_line}
                            {src.end_line && src.end_line !== src.start_line
                              ? `–${src.end_line}`
                              : ""}
                          </span>
                        )}
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {status === "failed" && (
            <p className="text-xs font-mono text-red-400 border-t border-zinc-800 pt-4">
              Ingestion failed — check the repo is public and try again.
            </p>
          )}
        </div>
      </div>
    </main>
  );
}