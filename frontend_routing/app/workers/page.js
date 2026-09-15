"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const STATUS_STYLE = {
  running: "border-sky-700/60 bg-sky-950/60 text-sky-300 shadow-[0_0_12px_rgba(56,189,248,0.2)]",
  completed: "border-emerald-700/60 bg-emerald-950/60 text-emerald-300",
  cancelled: "border-amber-700/60 bg-amber-950/60 text-amber-300",
  idle: "border-zinc-700 bg-zinc-800 text-zinc-400",
};

const TOOL_OPTIONS = [
  { name: "list_directory", label: "list_directory" },
  { name: "read_file", label: "read_file" },
  { name: "write_file", label: "write_file" },
  { name: "create_file", label: "create_file" },
  { name: "create_folder", label: "create_folder" },
  { name: "exists", label: "exists" },
  { name: "search_content", label: "search_content" },
  { name: "search_files", label: "search_files" },
  { name: "delete_file", label: "delete_file" },
];

const DEFAULT_TOOLS = TOOL_OPTIONS.map((t) => t.name);

function ForkForm() {
  const router = useRouter();
  const [objective, setObjective] = useState("");
  const [fsScope, setFsScope] = useState("D:/Ai automation backend");
  const [tools, setTools] = useState(DEFAULT_TOOLS);
  const [maxSteps, setMaxSteps] = useState(20);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [isOpen, setIsOpen] = useState(true);

  function toggleTool(name) {
    setTools((t) => (t.includes(name) ? t.filter((x) => x !== name) : [...t, name]));
  }

  function applyPreset(type) {
    if (type === "implement") {
      setObjective("Implement new feature, write clean code, and verify tests pass");
      setTools(["list_directory", "read_file", "write_file", "create_file", "exists"]);
    } else if (type === "refactor") {
      setObjective("Refactor code module to improve structure and maintain existing tests");
      setTools(["list_directory", "read_file", "write_file", "search_content", "search_files"]);
    } else if (type === "files") {
      setObjective("Inspect directory structure and check file existence");
      setTools(["list_directory", "exists", "search_files"]);
    }
  }

  async function submit(e) {
    e.preventDefault();
    if (!objective.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/workers/fork`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          objective: objective.trim(),
          worker_type: "opencode_worker",
          fs_scope: fsScope.trim() || "D:/Ai automation backend",
          allowed_tools: tools,
          max_steps: Math.max(1, Number(maxSteps) || 20),
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      router.push(`/worker/${data.session_id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mb-8 overflow-hidden rounded-2xl border border-zinc-800/80 bg-zinc-900/80 shadow-xl backdrop-blur-md">
      <div
        className="flex cursor-pointer items-center justify-between border-b border-zinc-800/60 p-4 transition hover:bg-zinc-800/30"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center gap-2.5">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-purple-950/80 text-purple-300 border border-purple-800/50 text-xs font-bold">
            ⚡
          </span>
          <div>
            <h2 className="text-sm font-semibold text-white">Fork a New Background Worker</h2>
            <p className="text-xs text-zinc-400">
              Spin up an isolated autonomous worker with strict scope & allowed tools
            </p>
          </div>
        </div>
        <button
          type="button"
          className="rounded-lg border border-zinc-800 px-2.5 py-1 text-xs text-zinc-400 transition hover:text-white"
        >
          {isOpen ? "Collapse" : "Expand Form"}
        </button>
      </div>

      {isOpen && (
        <form onSubmit={submit} className="p-5">
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <span className="text-xs font-medium text-zinc-400">Quick Presets:</span>
            <button
              type="button"
              onClick={() => applyPreset("implement")}
              className="rounded-lg border border-sky-800/50 bg-sky-950/40 px-2.5 py-1 text-xs font-medium text-sky-300 transition hover:bg-sky-900/50"
            >
              ✨ Implement Feature
            </button>
            <button
              type="button"
              onClick={() => applyPreset("refactor")}
              className="rounded-lg border border-purple-800/50 bg-purple-950/30 px-2.5 py-1 text-xs font-medium text-purple-300 transition hover:bg-purple-900/40"
            >
              🛠️ Refactor Module
            </button>
            <button
              type="button"
              onClick={() => applyPreset("files")}
              className="rounded-lg border border-zinc-700 bg-zinc-800/40 px-2.5 py-1 text-xs font-medium text-zinc-300 transition hover:bg-zinc-800"
            >
              📁 File Inspection
            </button>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-xs font-medium text-zinc-300">Task Objective</label>
              <input
                value={objective}
                onChange={(e) => setObjective(e.target.value)}
                placeholder='e.g. "Implement user authentication endpoints and write unit tests"'
                className="mt-1 w-full rounded-xl border border-zinc-800 bg-zinc-950/80 px-3.5 py-2.5 text-sm text-zinc-100 placeholder-zinc-500 outline-none transition focus:border-purple-600/70 focus:ring-1 focus:ring-purple-600/40"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-zinc-300">Filesystem Scope (`fs_scope` boundary)</label>
              <input
                value={fsScope}
                onChange={(e) => setFsScope(e.target.value)}
                placeholder="Absolute path boundary the worker is restricted to"
                className="mt-1 w-full rounded-xl border border-zinc-800 bg-zinc-950/80 px-3.5 py-2 font-mono text-xs text-zinc-200 outline-none transition focus:border-purple-600/70"
              />
            </div>
          </div>

          <div className="mt-4">
            <label className="text-xs font-medium text-zinc-300">Allowed Tools ({tools.length} selected)</label>
            <div className="mt-2 flex flex-wrap gap-2">
              {TOOL_OPTIONS.map((t) => (
                <label
                  key={t.name}
                  className={`cursor-pointer rounded-lg border px-2.5 py-1 text-xs font-medium transition ${
                    tools.includes(t.name)
                      ? "border-purple-700/70 bg-purple-950/50 text-purple-200 shadow-sm"
                      : "border-zinc-800 bg-zinc-950/50 text-zinc-400 hover:border-zinc-700 hover:text-zinc-200"
                  }`}
                >
                  <input
                    type="checkbox"
                    className="hidden"
                    checked={tools.includes(t.name)}
                    onChange={() => toggleTool(t.name)}
                  />
                  {t.label}
                </label>
              ))}
            </div>
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-zinc-800/60 pt-4">
            <label className="flex items-center gap-2 text-xs text-zinc-400">
              Max Steps
              <input
                type="number"
                min={1}
                max={50}
                value={maxSteps}
                onChange={(e) => setMaxSteps(e.target.value)}
                className="w-20 rounded-lg border border-zinc-800 bg-zinc-950 px-2.5 py-1 text-xs font-mono text-white outline-none focus:border-purple-500"
              />
            </label>
            <button
              type="submit"
              disabled={busy || !objective.trim() || tools.length === 0}
              className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 px-5 py-2 text-xs font-semibold text-white shadow-md shadow-purple-950/40 transition hover:from-purple-500 hover:to-indigo-500 disabled:opacity-40"
            >
              {busy ? "Forking..." : "⚡ Launch Worker"}
            </button>
          </div>

          {error && (
            <p className="mt-3 rounded-lg border border-red-900/60 bg-red-950/40 p-2.5 text-xs text-red-400">
              {error}
            </p>
          )}
        </form>
      )}
    </div>
  );
}

export default function WorkersPage() {
  const [workers, setWorkers] = useState([]);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [launchingTerminal, setLaunchingTerminal] = useState(false);
  const [terminalMsg, setTerminalMsg] = useState(null);

  async function openOpenCodeTerminal(dir = "D:/Ai automation backend") {
    setLaunchingTerminal(true);
    setTerminalMsg(null);
    try {
      const res = await fetch(`${API_URL}/workers/open-terminal`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ directory: dir }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setTerminalMsg(data.message || "✓ OpenCode CLI window launched on your desktop!");
      setTimeout(() => setTerminalMsg(null), 5000);
    } catch (e) {
      setTerminalMsg(`Failed: ${e.message}`);
      setTimeout(() => setTerminalMsg(null), 5000);
    } finally {
      setLaunchingTerminal(false);
    }
  }

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const res = await fetch(`${API_URL}/workers/list`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!cancelled) {
          setWorkers(data.workers || []);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) setError(e.message);
      }
    }

    poll();
    const id = setInterval(poll, 2000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const filtered = useMemo(() => {
    return workers.filter((w) => {
      const matchesStatus = filterStatus === "all" || w.status === filterStatus;
      const text = `${w.session_id} ${w.objective || ""}`.toLowerCase();
      const matchesSearch = !search || text.includes(search.toLowerCase());
      return matchesStatus && matchesSearch;
    });
  }, [workers, filterStatus, search]);

  const runningCount = workers.filter((w) => w.status === "running").length;

  return (
    <div className="flex h-screen flex-col bg-zinc-950 text-zinc-100">
      <header className="flex items-center justify-between border-b border-zinc-800/80 bg-zinc-900/50 px-6 py-3.5 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-500 shadow-md shadow-purple-950/40">
            <span className="text-sm font-bold text-white">⚡</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-semibold text-white tracking-tight">Worker Sessions</h1>
              {runningCount > 0 && (
                <span className="flex items-center gap-1.5 rounded-full border border-sky-800/60 bg-sky-950/60 px-2 py-0.5 text-[11px] font-medium text-sky-300">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-sky-400" />
                  {runningCount} active
                </span>
              )}
            </div>
            <p className="text-xs text-zinc-400">
              Real-time monitoring and management of delegated tasks
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => openOpenCodeTerminal()}
            disabled={launchingTerminal}
            className="inline-flex items-center gap-1.5 rounded-xl border border-sky-700/60 bg-sky-950/60 px-3.5 py-1.5 text-xs font-semibold text-sky-300 shadow-sm transition hover:border-sky-500 hover:bg-sky-900/60 hover:text-white disabled:opacity-40"
          >
            <span>💻</span>
            <span>{launchingTerminal ? "Opening..." : "Open OpenCode CLI"}</span>
          </button>
          <Link
            href="/"
            className="rounded-xl border border-zinc-800 bg-zinc-900/80 px-3.5 py-1.5 text-xs font-medium text-zinc-300 transition hover:border-zinc-700 hover:bg-zinc-800 hover:text-white"
          >
            ← Parent Chat
          </Link>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="mx-auto max-w-4xl">
          {terminalMsg && (
            <div className="mb-6 flex items-center justify-between rounded-xl border border-sky-800/60 bg-sky-950/60 p-3.5 text-xs font-medium text-sky-200 shadow-lg backdrop-blur-md">
              <div className="flex items-center gap-2">
                <span>💻</span>
                <span>{terminalMsg}</span>
              </div>
              <button
                onClick={() => setTerminalMsg(null)}
                className="text-zinc-400 hover:text-white"
              >
                ✕
              </button>
            </div>
          )}

          {error && (
            <div className="mb-6 rounded-xl border border-red-900/60 bg-red-950/40 p-4 text-xs text-red-300">
              Cannot reach backend at {API_URL}: {error}
            </div>
          )}

          {/* Direct Launch OpenCode Hero Card */}
          <div className="mb-6 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-sky-800/50 bg-gradient-to-r from-sky-950/30 to-indigo-950/20 p-4 shadow-xl backdrop-blur-md">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-900/60 border border-sky-700/50 text-sky-300 text-lg shadow-inner">
                💻
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Direct OpenCode Interactive CLI</h3>
                <p className="text-xs text-zinc-400">Launch a live terminal window on your desktop to chat with OpenCode directly.</p>
              </div>
            </div>
            <button
              onClick={() => openOpenCodeTerminal()}
              disabled={launchingTerminal}
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-sky-600 to-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-md shadow-sky-950/40 transition hover:from-sky-500 hover:to-indigo-500 disabled:opacity-40"
            >
              <span>▶</span>
              <span>{launchingTerminal ? "Opening Terminal..." : "Launch OpenCode on Desktop"}</span>
            </button>
          </div>

          <ForkForm />


          {/* List Controls */}
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-1.5 rounded-xl border border-zinc-800 bg-zinc-900/60 p-1">
              {["all", "running", "completed", "cancelled"].map((st) => (
                <button
                  key={st}
                  onClick={() => setFilterStatus(st)}
                  className={`rounded-lg px-2.5 py-1 text-xs font-medium capitalize transition ${
                    filterStatus === st
                      ? "bg-purple-950/80 text-purple-200 border border-purple-800/50 shadow-sm"
                      : "text-zinc-400 hover:text-white"
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>

            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search workers or objectives..."
              className="rounded-xl border border-zinc-800 bg-zinc-900/70 px-3 py-1.5 text-xs text-zinc-200 placeholder-zinc-500 outline-none focus:border-purple-600/60"
            />
          </div>

          {filtered.length === 0 && (
            <div className="my-16 text-center text-zinc-500 text-xs">
              {workers.length === 0
                ? "No worker sessions yet. Use the form above or tell the chat agent to 'fork a task'."
                : "No worker sessions matching the filter."}
            </div>
          )}

          <div className="space-y-3">
            {filtered.map((w) => (
              <Link
                key={w.session_id}
                href={`/worker/${w.session_id}`}
                className="group block rounded-2xl border border-zinc-800/80 bg-zinc-900/70 p-4 shadow-md transition hover:border-purple-800/50 hover:bg-zinc-900/95"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="rounded-md border border-purple-900/60 bg-purple-950/50 px-2 py-0.5 font-mono text-[11px] font-semibold text-purple-300">
                        {w.session_id}
                      </span>
                      <h3 className="truncate text-sm font-semibold text-white group-hover:text-purple-200 transition">
                        {w.objective || "Untitled Worker Task"}
                      </h3>
                    </div>

                    <p className="mt-1.5 text-xs text-zinc-400">
                      {w.completed?.length ?? 0} completed · {w.errors?.length ?? 0} errors
                      {w.current_step ? (
                        <span className="text-sky-400 font-medium"> · active step: {w.current_step}</span>
                      ) : ""}
                    </p>

                    {w.allowed_tools && w.allowed_tools.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {[...new Set(w.allowed_tools)].slice(0, 5).map((tool, idx) => (
                          <span
                            key={`${tool}-${idx}`}
                            className="rounded bg-zinc-950/80 px-1.5 py-0.5 font-mono text-[10px] text-zinc-400 border border-zinc-800/50"
                          >
                            {tool}
                          </span>
                        ))}
                        {w.allowed_tools.length > 5 && (
                          <span className="text-[10px] text-zinc-500 self-center">
                            +{w.allowed_tools.length - 5} more
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="flex shrink-0 flex-col items-end gap-2.5">
                    <span
                      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider ${
                        STATUS_STYLE[w.status] || STATUS_STYLE.idle
                      }`}
                    >
                      {w.status === "running" && (
                        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-sky-400" />
                      )}
                      {w.status}
                    </span>

                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-zinc-800">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-purple-500 to-sky-400 transition-all duration-300"
                          style={{ width: `${w.progress_percent ?? 0}%` }}
                        />
                      </div>
                      <span className="font-mono text-[11px] text-zinc-400">
                        {w.progress_percent ?? 0}%
                      </span>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}