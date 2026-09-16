"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { UserBubble, BotMessage } from "./components/Chat";
import VoiceInput from "./components/VoiceInput";

function getApiUrl() {
  if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
  if (typeof window !== "undefined") {
    const proto = window.location.protocol;
    const host = window.location.hostname;
    return `${proto}//${host}:8000`;
  }
  return "http://127.0.0.1:8000";
}

const CHAT_STORAGE_KEY = "jarvis_chat_messages";

function generateId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function loadStoredMessages() {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.sessionStorage.getItem(CHAT_STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((m) => m && !m.thinking);
  } catch {
    return [];
  }
}

const SUGGESTIONS = [
  { label: "⚡ Fork Heading Normalization", prompt: "fork the task: normalize headings on my report.docx" },
  { label: "📂 List files", prompt: "list files in D:/Ai automation backend" },
  { label: "✉️ Recent emails", prompt: "list my recent emails" },
  { label: "💬 WhatsApp chats", prompt: "list my whatsapp chats" },
];

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [mounted, setMounted] = useState(false);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [backendOnline, setBackendOnline] = useState(null);
  const [confirmedPlanIds, setConfirmedPlanIds] = useState(new Set());
  const endRef = useRef(null);

  // Load stored messages after mount to prevent hydration mismatch
  useEffect(() => {
    setMounted(true);
    setMessages(loadStoredMessages());
  }, []);

  // Check backend health
  useEffect(() => {
    async function checkHealth() {
      const baseUrl = getApiUrl();
      try {
        const res = await fetch(`${baseUrl}/health`);
        setBackendOnline(res.ok);
      } catch {
        setBackendOnline(false);
      }
    }
    checkHealth();
    const id = setInterval(checkHealth, 10000);
    return () => clearInterval(id);
  }, []);

  // Keep chat across reloads
  useEffect(() => {
    if (!mounted) return;
    try {
      window.sessionStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages));
    } catch {
      // storage full
    }
  }, [messages, mounted]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function callAgent(body) {
    const baseUrl = getApiUrl();
    let res;
    try {
      res = await fetch(`${baseUrl}/agent/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    } catch (netErr) {
      throw new Error(`Cannot reach Jarvis backend (${baseUrl}). Please check if the backend is running.`);
    }

    let data;
    try {
      data = await res.json();
    } catch {
      throw new Error(`Server returned status ${res.status}`);
    }

    if (!res.ok) {
      throw new Error(data.detail || data.message || `Request failed (${res.status})`);
    }
    return data;
  }

  async function sendPrompt(text) {
    const prompt = text.trim();
    if (!prompt || busy) return;

    const botId = generateId();
    setMessages((m) => [
      ...m,
      { id: generateId(), role: "user", content: prompt, prompt },
      { id: botId, role: "bot", prompt, thinking: true },
    ]);
    setInput("");
    setBusy(true);

    try {
      const result = await callAgent({ prompt });
      setMessages((m) =>
        m.map((msg) =>
          msg.id === botId ? { ...msg, thinking: false, data: result } : msg
        )
      );
    } catch (e) {
      setMessages((m) =>
        m.map((msg) =>
          msg.id === botId ? { ...msg, thinking: false, error: e.message } : msg
        )
      );
    } finally {
      setBusy(false);
    }
  }

  async function confirmPlan(prompt, planId) {
    if (busy || confirmedPlanIds.has(planId)) return;
    setBusy(true);
    setConfirmedPlanIds((prev) => new Set([...prev, planId]));

    const botId = generateId();
    setMessages((m) => [...m, { id: botId, role: "bot", prompt, thinking: true }]);

    try {
      const result = await callAgent({ prompt, confirm: true, plan_id: planId });
      setMessages((m) =>
        m.map((msg) =>
          msg.id === botId ? { ...msg, thinking: false, data: result } : msg
        )
      );
    } catch (e) {
      setMessages((m) =>
        m.map((msg) =>
          msg.id === botId ? { ...msg, thinking: false, error: e.message } : msg
        )
      );
    } finally {
      setBusy(false);
    }
  }

  async function newChat() {
    setMessages([]);
    setConfirmedPlanIds(new Set());
    try {
      window.sessionStorage.removeItem(CHAT_STORAGE_KEY);
      const baseUrl = getApiUrl();
      await fetch(`${baseUrl}/agent/history?session_id=default`, { method: "DELETE" });
    } catch {
      // best effort
    }
  }

  return (
    <div className="flex h-screen flex-col bg-zinc-950 text-zinc-100 selection:bg-purple-500/30 selection:text-purple-200">
      <header className="flex items-center justify-between border-b border-zinc-800/80 bg-zinc-900/50 px-6 py-3.5 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-500 shadow-md shadow-purple-950/40">
            <span className="text-sm font-bold tracking-wider text-white">J</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-semibold text-white tracking-tight">Jarvis Assistant</h1>
              <span
                className={`flex h-2 w-2 rounded-full ${
                  backendOnline === null
                    ? "bg-zinc-500"
                    : backendOnline
                    ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]"
                    : "bg-red-400 shadow-[0_0_8px_rgba(248,113,113,0.8)]"
                }`}
                title={backendOnline ? "Backend online" : "Backend offline"}
              />
            </div>
            <p className="text-xs text-zinc-400">Agent & Worker Orchestrator</p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={newChat}
            disabled={busy}
            className="rounded-xl border border-zinc-800 bg-zinc-900/80 px-3.5 py-1.5 text-xs font-medium text-zinc-300 transition hover:border-zinc-700 hover:bg-zinc-800 hover:text-white disabled:opacity-40"
          >
            New Chat
          </button>
          <Link
            href="/workers"
            className="inline-flex items-center gap-1.5 rounded-xl border border-purple-800/60 bg-purple-950/40 px-3.5 py-1.5 text-xs font-medium text-purple-300 shadow-sm transition hover:border-purple-600 hover:bg-purple-900/50 hover:text-white"
          >
            <span>⚡ Workers</span>
            <span>→</span>
          </Link>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto flex max-w-2xl flex-col gap-4">
          {messages.length === 0 ? (
            <div className="my-auto flex flex-col items-center justify-center pt-16 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-purple-800/40 bg-purple-950/30 text-purple-300 shadow-inner">
                ⚡
              </div>
              <h2 className="mt-4 text-base font-semibold text-white">How can Jarvis assist you today?</h2>
              <p className="mt-1 text-xs text-zinc-400 max-w-sm">
                Ask anything, run file automation, send emails, or delegate complex tasks to specialized background workers.
              </p>

              <div className="mt-6 flex flex-wrap justify-center gap-2 max-w-lg">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s.label}
                    onClick={() => sendPrompt(s.prompt)}
                    className="rounded-xl border border-zinc-800/80 bg-zinc-900/60 px-3 py-1.5 text-xs text-zinc-300 transition hover:border-purple-700/60 hover:bg-zinc-800/80 hover:text-white"
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) =>
              msg.role === "user" ? (
                <UserBubble key={msg.id} content={msg.content || msg.prompt} />
              ) : (
                <BotMessage
                  key={msg.id}
                  msg={msg}
                  onConfirm={(prompt, planId) => confirmPlan(prompt, planId)}
                />
              )
            )
          )}
          <div ref={endRef} />
        </div>
      </div>

      <footer className="border-t border-zinc-800/80 bg-zinc-900/40 p-4 backdrop-blur-md">
        <div className="mx-auto flex max-w-2xl items-center gap-2.5">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendPrompt(input)}
            placeholder='Ask Jarvis, type a command, or click 🎙️ / Alt+V...'
            disabled={busy}
            className="flex-1 rounded-xl border border-zinc-800 bg-zinc-900/80 px-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-500 outline-none transition focus:border-purple-600/70 focus:ring-1 focus:ring-purple-600/50 disabled:opacity-50"
          />
          <VoiceInput
            disabled={busy}
            onTranscriptInsert={(text) => {
              setInput((prev) => (prev ? `${prev} ${text}` : text));
            }}
            onAutoSend={(text) => {
              sendPrompt(text);
            }}
          />
          <button
            onClick={() => sendPrompt(input)}
            disabled={busy || !input.trim()}
            className="rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 px-5 py-2.5 text-sm font-medium text-white shadow-md shadow-purple-950/40 transition hover:from-purple-500 hover:to-indigo-500 disabled:opacity-40"
          >
            Send
          </button>
        </div>
      </footer>
    </div>
  );
}