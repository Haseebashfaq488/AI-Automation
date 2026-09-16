"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import VoiceInput from "../../components/VoiceInput";
import ToolOutputViewer from "../../components/ToolOutputViewer";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const EVENT_STYLE = {
  WORK_STARTED: "text-sky-400",
  STEP_STARTED: "text-zinc-300",
  STEP_COMPLETED: "text-emerald-400",
  STEP_FAILED: "text-red-400",
  VALIDATION_STARTED: "text-yellow-400",
  VALIDATION_FAILED: "text-red-400",
  RECOVERY_STARTED: "text-orange-400",
  RECOVERY_COMPLETED: "text-emerald-400",
  PARENT_INTERVENTION: "text-purple-400",
  WORK_COMPLETED: "text-sky-300",
};

const STATUS_STYLE = {
  running: "border-sky-500/30 bg-sky-950/60 text-sky-300",
  completed: "border-emerald-500/30 bg-emerald-950/60 text-emerald-300",
  cancelled: "border-amber-500/30 bg-amber-950/60 text-amber-300",
  idle: "border-zinc-700/40 bg-zinc-900/60 text-zinc-400",
};

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

export default function WorkerPage() {
  const params = useParams();
  const sessionId = params?.id;

  const [state, setState] = useState(null);
  const [events, setEvents] = useState([]);
  const [artifacts, setArtifacts] = useState([]);
  const [intervention, setIntervention] = useState("");
  const [copiedId, setCopiedId] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const eventsEndRef = useRef(null);
  const eventSourceRef = useRef(null);

  // ── 1. Fetch artifacts ────────────────────────────────────────────────
  const fetchArtifacts = useCallback(async () => {
    if (!sessionId) return;
    try {
      const res = await fetch(`${API_URL}/workers/${sessionId}/artifacts`);
      if (res.ok) {
        const data = await res.json();
        setArtifacts(data.artifacts || []);
      }
    } catch {
      /* ignore background fetch errors */
    }
  }, [sessionId]);

  // ── 2. Poll worker state ─────────────────────────────────────────────
  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;

    async function poll() {
      try {
        const res = await fetch(`${API_URL}/workers/${sessionId}`);
        if (res.status === 404) {
          if (!cancelled) setNotFound(true);
          return;
        }
        if (!res.ok) return;
        const data = await res.json();
        if (!cancelled) {
          setState(data);
          // If finished, refresh artifacts and we can slow down or stop polling
          if (data.status === "completed" || data.status === "cancelled") {
            fetchArtifacts();
          }
        }
      } catch {
        /* backend unreachable — keep last state */
      }
    }

    poll();
    fetchArtifacts();

    const id = setInterval(() => {
      // Only keep fast poll if running
      poll();
    }, 2000);

    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [sessionId, fetchArtifacts]);

  // ── 3. SSE event stream with auto-close on WORK_COMPLETED ────────────
  useEffect(() => {
    if (!sessionId) return;
    const seen = new Set();

    function pushEvent(raw) {
      try {
        const evt = JSON.parse(raw);
        const key = `${evt.type}:${JSON.stringify(evt.data)}`;
        if (seen.has(key)) return;
        seen.add(key);
        setEvents((prev) => [...prev, evt]);

        if (evt.type === "WORK_COMPLETED") {
          fetchArtifacts();
          // Cleanly close EventSource to prevent endless reconnection loops
          if (eventSourceRef.current) {
            eventSourceRef.current.close();
          }
        }
      } catch {
        /* ignore malformed lines (comments / heartbeats) */
      }
    }

    const source = new EventSource(`${API_URL}/workers/${sessionId}/events`);
    eventSourceRef.current = source;

    source.onmessage = (msg) => pushEvent(msg.data);
    source.onerror = () => {
      // If already finished, close permanently
      if (state?.status === "completed" || state?.status === "cancelled") {
        source.close();
      }
    };

    return () => {
      source.close();
    };
  }, [sessionId, state?.status, fetchArtifacts]);

  // Auto-scroll raw events feed
  useEffect(() => {
    eventsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  const sendIntervention = useCallback(async () => {
    const message = intervention.trim();
    if (!message) return;
    setIntervention("");
    try {
      await fetch(`${API_URL}/workers/${sessionId}/intervene`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
    } catch {
      /* ignore */
    }
  }, [intervention, sessionId]);

  const cancelWorker = useCallback(async () => {
    setCancelling(true);
    try {
      await fetch(`${API_URL}/workers/${sessionId}/cancel`, { method: "POST" });
    } catch {
      /* ignore */
    } finally {
      setCancelling(false);
    }
  }, [sessionId]);

  const [launchingTerminal, setLaunchingTerminal] = useState(false);
  const [terminalMsg, setTerminalMsg] = useState(null);

  const openOpenCodeTerminal = useCallback(async () => {
    setLaunchingTerminal(true);
    setTerminalMsg(null);
    try {
      const res = await fetch(`${API_URL}/workers/open-terminal`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ directory: state?.fs_scope || "D:/Ai automation backend" }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setTerminalMsg(data.message || "✓ OpenCode CLI window opened on desktop!");
      setTimeout(() => setTerminalMsg(null), 5000);
    } catch (e) {
      setTerminalMsg(`Failed: ${e.message}`);
      setTimeout(() => setTerminalMsg(null), 5000);
    } finally {
      setLaunchingTerminal(false);
    }
  }, [state?.fs_scope]);

  const copySessionId = useCallback(() => {
    navigator.clipboard.writeText(sessionId);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  }, [sessionId]);

  if (notFound) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4 bg-zinc-950 text-white">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-8 text-center shadow-xl backdrop-blur-md">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-red-950/60 text-red-400">
            ✕
          </div>
          <h2 className="text-lg font-semibold text-zinc-100">Worker Not Found</h2>
          <p className="mt-1 text-sm text-zinc-400">
            Session <span className="font-mono text-zinc-300">{sessionId}</span> does not exist or has expired.
          </p>
          <Link
            href="/workers"
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-sky-600 px-4 py-2 text-xs font-semibold text-white shadow-md transition hover:bg-sky-500"
          >
            ← Back to Worker Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const currentEvent = [...events].reverse().find((e) => e.type !== "WORK_COMPLETED");
  const nowDoing = state?.current_step || currentEvent?.data?.step || null;

  return (
    <div className="flex h-screen flex-col bg-zinc-950 text-white selection:bg-purple-500/30">
      {/* ── Top Bar ── */}
      <header className="flex shrink-0 items-center justify-between border-b border-zinc-800/80 bg-zinc-900/40 px-6 py-3.5 backdrop-blur-md">
        <div className="flex items-center gap-4">
          <Link
            href="/workers"
            className="group flex items-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-900/80 px-3 py-1.5 text-xs font-medium text-zinc-300 transition hover:border-zinc-700 hover:text-white"
          >
            <span className="transition-transform group-hover:-translate-x-0.5">←</span>
            <span>Workers</span>
          </Link>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-zinc-400">session /</span>
              <h1 className="font-mono text-sm font-semibold text-zinc-100">{sessionId}</h1>
            </div>
            <button
              onClick={copySessionId}
              title="Copy Session ID"
              className="rounded-md border border-zinc-800 bg-zinc-900/60 px-2 py-0.5 text-[11px] font-mono text-zinc-400 transition hover:border-zinc-700 hover:text-zinc-200"
            >
              {copiedId ? "✓ Copied" : "Copy"}
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={openOpenCodeTerminal}
            disabled={launchingTerminal}
            className="inline-flex items-center gap-1.5 rounded-lg border border-sky-700/60 bg-sky-950/60 px-3 py-1.5 text-xs font-semibold text-sky-300 shadow-sm transition hover:border-sky-500 hover:bg-sky-900/60 hover:text-white disabled:opacity-40"
          >
            <span>💻</span>
            <span>{launchingTerminal ? "Opening..." : "Open OpenCode CLI"}</span>
          </button>

          <span
            className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium ${
              STATUS_STYLE[state?.status] || STATUS_STYLE.idle
            }`}
          >
            {state?.status === "running" && (
              <span className="h-2 w-2 animate-pulse rounded-full bg-sky-400" />
            )}
            {state?.status === "completed" && (
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
            )}
            {state?.status === "cancelled" && (
              <span className="h-2 w-2 rounded-full bg-amber-400" />
            )}
            {state?.status || "connecting…"}
          </span>

          {state?.status === "running" && (
            <button
              onClick={cancelWorker}
              disabled={cancelling}
              className="rounded-lg border border-red-900/60 bg-red-950/40 px-3 py-1.5 text-xs font-medium text-red-300 transition hover:bg-red-900/60 disabled:opacity-50"
            >
              {cancelling ? "Cancelling…" : "Cancel Worker"}
            </button>
          )}
        </div>
      </header>


      {/* ── Main Two-Column View ── */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Column: Execution Details & Chat Feed */}
        <div className="flex-1 overflow-y-auto px-6 py-6 scrollbar-thin">
          <div className="mx-auto flex max-w-3xl flex-col gap-5">
            {/* Task Contract Card */}
            <ContractCard state={state} sessionId={sessionId} />

            {/* Artifacts Download Panel */}
            <ArtifactsPanel artifacts={artifacts} sessionId={sessionId} />

            {/* Step Bubbles */}
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between px-1">
                <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
                  Execution Trace
                </span>
                <span className="text-xs text-zinc-500">
                  {events.filter((e) => e.type.startsWith("STEP_")).length} step events
                </span>
              </div>

              {events
                .filter((e) => e.type.startsWith("STEP_") || e.type === "PARENT_INTERVENTION")
                .map((e, i) => (
                  <StepBubble key={i} event={e} />
                ))}

              {events.length === 0 && (
                <div className="flex items-center justify-center rounded-2xl border border-dashed border-zinc-800/80 p-8 text-center text-xs text-zinc-500">
                  Waiting for worker to start execution…
                </div>
              )}
            </div>

            {/* Result Card when completed */}
            {events.some((e) => e.type === "WORK_COMPLETED") && (
              <ResultCard
                event={events.find((e) => e.type === "WORK_COMPLETED")}
                artifactsCount={artifacts.length}
              />
            )}
          </div>
        </div>

        {/* Right Sidebar: Live State & Intervention */}
        <aside className="flex w-84 shrink-0 flex-col border-l border-zinc-800/80 bg-zinc-900/30">
          {/* Progress & Current Step */}
          <div className="border-b border-zinc-800/80 p-4">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Active Step
              </p>
              <span className="font-mono text-xs font-semibold text-sky-400">
                {state?.progress_percent ?? 0}%
              </span>
            </div>

            <div className="mt-2.5 flex items-start gap-2">
              {state?.status === "running" ? (
                <span className="mt-1 h-2 w-2 shrink-0 animate-pulse rounded-full bg-sky-400" />
              ) : (
                <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-zinc-600" />
              )}
              <p className="text-sm font-medium text-zinc-200">
                {nowDoing || (state?.status === "completed" ? "All steps finished" : "Waiting…")}
              </p>
            </div>

            {/* Progress Bar */}
            <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-zinc-800/80">
              <div
                className="h-full rounded-full bg-gradient-to-r from-sky-500 to-purple-500 transition-all duration-500"
                style={{ width: `${state?.progress_percent ?? 0}%` }}
              />
            </div>
          </div>

          {/* Checklist */}
          <div className="border-b border-zinc-800/80 p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Checklist
            </p>
            <div className="mt-2.5 max-h-48 overflow-y-auto space-y-1.5 pr-1">
              {(state?.completed || []).map((c, i) => (
                <div key={`comp-${i}`} className="flex items-start gap-2 text-xs text-emerald-400">
                  <span className="shrink-0 font-bold">✓</span>
                  <span className="line-clamp-2 text-zinc-300">{c}</span>
                </div>
              ))}
              {(state?.errors || []).map((e, i) => (
                <div key={`err-${i}`} className="flex items-start gap-2 text-xs text-red-400">
                  <span className="shrink-0 font-bold">✗</span>
                  <span className="line-clamp-2">{e}</span>
                </div>
              ))}
              {(state?.completed || []).length === 0 && (state?.errors || []).length === 0 && (
                <p className="text-xs text-zinc-600 italic">No checklist items recorded yet</p>
              )}
            </div>
          </div>

          {/* Raw SSE Event Stream */}
          <div className="flex flex-1 flex-col overflow-hidden p-4">
            <div className="flex items-center justify-between pb-2">
              <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Live Event Bus
              </p>
              <span className="font-mono text-[10px] text-zinc-500">{events.length}</span>
            </div>
            <div className="flex-1 overflow-y-auto rounded-xl border border-zinc-800/70 bg-zinc-950/80 p-2.5 font-mono text-[11px]">
              <ul className="space-y-1">
                {events.map((e, i) => (
                  <li key={i} className={`truncate ${EVENT_STYLE[e.type] || "text-zinc-400"}`}>
                    <span className="text-zinc-600 mr-1.5">{i + 1}</span>
                    <span className="font-medium">{e.type}</span>
                    {e.data?.step && (
                      <span className="ml-1 text-zinc-400">· {e.data.step}</span>
                    )}
                  </li>
                ))}
                <div ref={eventsEndRef} />
              </ul>
            </div>
          </div>

          {/* Intervention Panel (Parent Agent Control) */}
          {state?.status === "running" && (
            <div className="border-t border-zinc-800/80 bg-zinc-900/40 p-4">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold uppercase tracking-wider text-purple-400">
                  ⚡ Intervene (Parent Agent)
                </p>
              </div>
              <p className="mt-1 text-[11px] text-zinc-400">
                Send instructions directly into the running worker's next prompt loop.
              </p>
              <div className="mt-2.5 flex items-center gap-2">
                <input
                  value={intervention}
                  onChange={(e) => setIntervention(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendIntervention()}
                  placeholder="e.g. Skip table formatting, focus on Heading 1..."
                  className="flex-1 rounded-xl border border-zinc-700/80 bg-zinc-950 px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 outline-none focus:border-purple-500 transition"
                />
                <VoiceInput
                  onTranscriptInsert={(text) =>
                    setIntervention((prev) => (prev ? `${prev} ${text}` : text))
                  }
                  onAutoSend={async (text) => {
                    setIntervention(text);
                    try {
                      await fetch(`${API_URL}/workers/${sessionId}/intervene`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ message: text }),
                      });
                      setIntervention("");
                    } catch {
                      // ignore
                    }
                  }}
                />
                <button
                  onClick={sendIntervention}
                  disabled={!intervention.trim()}
                  className="rounded-xl bg-purple-600 px-3.5 py-2 text-xs font-semibold text-white shadow-md transition hover:bg-purple-500 disabled:opacity-40"
                >
                  Send
                </button>
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

// ── Contract Card Component ─────────────────────────────────────────────
function ContractCard({ state, sessionId }) {
  return (
    <div className="rounded-2xl border border-zinc-800/80 bg-zinc-900/60 p-5 shadow-xl backdrop-blur-md">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-sky-950 text-xs text-sky-400">
              📋
            </span>
            <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Task Contract
            </p>
          </div>
          <h2 className="mt-2 text-base font-semibold text-zinc-100">
            {state?.objective || "Forked Autonomous Task"}
          </h2>
        </div>

        {state?.max_steps && (
          <div className="text-right">
            <span className="rounded-md border border-zinc-800 bg-zinc-950 px-2 py-1 font-mono text-xs text-zinc-400">
              Budget: {state.max_steps} steps
            </span>
          </div>
        )}
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-zinc-800/50 bg-zinc-950/60 p-3">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
            Filesystem Scope
          </p>
          <p className="mt-1 truncate font-mono text-xs text-zinc-300" title={state?.fs_scope}>
            {state?.fs_scope || "—"}
          </p>
        </div>


      </div>
    </div>
  );
}

// ── Artifacts Panel Component ───────────────────────────────────────────
function ArtifactsPanel({ artifacts, sessionId }) {
  if (!artifacts || artifacts.length === 0) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-purple-900/40 bg-purple-950/10 p-5 shadow-xl backdrop-blur-md">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-purple-900/60 text-xs text-purple-300">
            📦
          </span>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-purple-300">
            Generated Artifacts ({artifacts.length})
          </h3>
        </div>
        <span className="text-xs text-purple-400/80">Available for direct download</span>
      </div>

      <div className="mt-3 grid grid-cols-1 gap-2.5 sm:grid-cols-2">
        {artifacts.map((art) => (
          <div
            key={art.name}
            className="flex items-center justify-between gap-3 rounded-xl border border-purple-800/30 bg-zinc-950/70 p-3 transition hover:border-purple-600/50"
          >
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-zinc-100" title={art.name}>
                {art.name}
              </p>
              <p className="text-xs text-zinc-500">{formatBytes(art.size_bytes)}</p>
            </div>
            <a
              href={`${API_URL}/workers/${sessionId}/artifacts/${encodeURIComponent(art.name)}`}
              download={art.name}
              className="inline-flex shrink-0 items-center gap-1 rounded-lg bg-purple-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition hover:bg-purple-500"
            >
              <span>Download</span>
              <span>↓</span>
            </a>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Step Bubble Component ───────────────────────────────────────────────
function StepBubble({ event }) {
  const [showDetails, setShowDetails] = useState(false);

  if (event.type === "PARENT_INTERVENTION") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-md border border-purple-900/60 bg-purple-950/70 px-4 py-3 text-sm text-purple-200 shadow-md">
          <div className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-purple-400">
            <span>⚡ Parent Intervention</span>
          </div>
          <p className="mt-1 text-sm font-medium">{event.data?.message}</p>
        </div>
      </div>
    );
  }

  const ok = event.type === "STEP_COMPLETED";
  const failed = event.type === "STEP_FAILED";
  const running = event.type === "STEP_STARTED";
  const outputData = event.data?.output || event.data?.result;

  const isMilestone =
    event.data?.step?.startsWith("milestone_") ||
    outputData?.milestone ||
    outputData?.phase;

  const phaseName =
    outputData?.phase ||
    (event.data?.step?.startsWith("milestone_")
      ? event.data.step.replace("milestone_", "")
      : "");

  const milestoneTitle =
    outputData?.milestone ||
    event.data?.step?.replace("milestone_", "Milestone: ") ||
    "Execution Step";

  const previewText = outputData?.output_preview || (typeof outputData === "string" ? outputData : null);

  return (
    <div className="flex justify-start">
      <div
        className={`w-full max-w-[90%] rounded-2xl rounded-bl-md border px-4 py-3.5 text-sm shadow-md transition ${
          ok
            ? "border-emerald-900/60 bg-emerald-950/40 text-zinc-200"
            : failed
            ? "border-red-900/60 bg-red-950/40 text-red-200"
            : running
            ? "border-sky-900/60 bg-sky-950/30 text-zinc-200"
            : "border-zinc-800/80 bg-zinc-900/60 text-zinc-300"
        }`}
      >
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span
              className={`rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                ok
                  ? "bg-emerald-900/60 text-emerald-300"
                  : failed
                  ? "bg-red-900/60 text-red-300"
                  : running
                  ? "bg-sky-900/60 text-sky-300"
                  : "bg-zinc-800 text-zinc-400"
              }`}
            >
              {ok ? "✓ Completed" : failed ? "✗ Failed" : running ? "● Running" : event.type}
            </span>

            {isMilestone && (
              <span className="rounded bg-purple-950/80 border border-purple-800/50 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-purple-300">
                {outputData?.milestone_index && outputData?.total_milestones
                  ? `Phase ${outputData.milestone_index}/${outputData.total_milestones}`
                  : phaseName ? `Phase: ${phaseName}` : "Milestone"}
              </span>
            )}

            {outputData?.opencode_session && (
              <span className="rounded bg-zinc-900 px-2 py-0.5 font-mono text-[10px] text-zinc-400 border border-zinc-800">
                session: {outputData.opencode_session}
              </span>
            )}
          </div>
        </div>

        <h4 className="mt-2 text-sm font-semibold text-zinc-100">
          {milestoneTitle}
        </h4>

        {failed && event.data?.error && (
          <div className="mt-2 rounded-lg border border-red-900/60 bg-red-950/60 p-2.5 text-xs text-red-300">
            {event.data.error}
          </div>
        )}

        {/* Milestone Output Preview / Text */}
        {previewText && (
          <div className="mt-2.5 rounded-xl border border-zinc-800/70 bg-zinc-950/80 p-3 text-xs text-zinc-300 font-mono whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto">
            {previewText}
          </div>
        )}


        {/* Structured Output */}
        {outputData && typeof outputData === "object" && (
          <div className="mt-2.5">
            <ToolOutputViewer
              tool={event.data?.step?.replace(/^milestone_/, "") || ""}
              data={outputData}
            />
          </div>
        )}

        {/* Raw event data toggle */}
        {outputData && (
          <div className="mt-2">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="inline-flex items-center gap-1 text-[11px] font-medium text-zinc-500 hover:text-zinc-300 transition"
            >
              <span>{showDetails ? "Hide raw ▲" : "Inspect raw JSON ▼"}</span>
            </button>

            {showDetails && (
              <pre className="mt-1.5 max-h-48 overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-950/90 p-2.5 font-mono text-[11px] text-zinc-300">
                {typeof outputData === "string"
                  ? outputData
                  : JSON.stringify(outputData, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}


// ── Result Card Component ───────────────────────────────────────────────
function ResultCard({ event, artifactsCount }) {
  const success = event?.data?.success;
  return (
    <div
      className={`rounded-2xl border p-5 shadow-xl backdrop-blur-md ${
        success
          ? "border-emerald-800/60 bg-emerald-950/40"
          : "border-amber-800/60 bg-amber-950/40"
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span
            className={`flex h-8 w-8 items-center justify-center rounded-full text-base font-bold ${
              success ? "bg-emerald-900/80 text-emerald-300" : "bg-amber-900/80 text-amber-300"
            }`}
          >
            {success ? "✓" : "!"}
          </span>
          <div>
            <h3
              className={`text-sm font-semibold ${
                success ? "text-emerald-200" : "text-amber-200"
              }`}
            >
              {success ? "Worker Goal Completed Successfully" : "Worker Finished with Warnings"}
            </h3>
            <p className="text-xs text-zinc-400">
              Session execution finalized. Check artifacts and checklist above.
            </p>
          </div>
        </div>

        <Link
          href="/workers"
          className="rounded-xl border border-zinc-700 bg-zinc-800/80 px-3 py-1.5 text-xs font-semibold text-zinc-200 transition hover:bg-zinc-700"
        >
          All Workers →
        </Link>
      </div>

      {event?.data?.tools_used?.length > 0 && (
        <div className="mt-3.5 flex items-center gap-2 border-t border-zinc-800/60 pt-3">
          <span className="text-xs text-zinc-400">Tools invoked:</span>
          <div className="flex flex-wrap gap-1">
            {event.data.tools_used.map((t) => (
              <span
                key={t}
                className="rounded bg-zinc-800/80 px-1.5 py-0.5 font-mono text-[10px] text-zinc-300"
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}