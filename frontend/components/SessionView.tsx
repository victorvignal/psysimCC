"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  getSession,
  toggleTimer,
  sendMessage,
  type SessionState,
  type TimerInfo,
} from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  pending?: boolean;
}

const NIVEL = {
  iniciante:     { bg: "var(--green-bg)",  fg: "var(--green-fg)" },
  intermediario: { bg: "var(--yellow-bg)", fg: "var(--yellow-fg)" },
  avancado:      { bg: "var(--red-bg)",    fg: "var(--red-fg)" },
} as const;

export default function SessionView({ sessionId }: { sessionId: string }) {
  const router = useRouter();
  const [session, setSession] = useState<SessionState | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [timer, setTimer] = useState<TimerInfo | null>(null);
  const [showTimer, setShowTimer] = useState(false);
  const [supervisionMode, setSupervisionMode] = useState<"realtime" | "session" | "last3" | null>(null);
  const [supervisionPanelOpen, setSupervisionPanelOpen] = useState(false);
  const [supervisionContent, setSupervisionContent] = useState("");
  const [supervisionLoading, setSupervisionLoading] = useState(false);
  const [notes, setNotes] = useState("");
  const [approach, setApproach] = useState("TCC");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getSession(sessionId)
      .then((s) => { setSession(s); setTimer(s.timer); })
      .catch(() => router.replace("/"));
  }, [sessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    if (!input.trim() || streaming) return;
    const text = input.trim();
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    setStreaming(true);
    setMessages((m) => [...m, { role: "assistant", content: "", pending: true }]);

    try {
      const reply = await sendMessage(sessionId, text);
      setMessages((m) => {
        const last = m[m.length - 1];
        if (!last) return m;
        return [...m.slice(0, -1), { ...last, content: reply, pending: false }];
      });
    } catch {
      setMessages((m) => m.slice(0, -1));
    } finally {
      setStreaming(false);
    }
  }

  async function handleToggleTimer() {
    if (!timer) {
      // Start the timer if not running
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/sessions/${sessionId}/timer/start`, { method: "POST" });
        if (res.ok) {
          const data = await res.json();
          setTimer(data.timer);
          setShowTimer(true);
        }
      } catch { /* ignore */ }
      return;
    }
    setShowTimer(v => !v);
  }

  function getHistorySlice(mode: "realtime" | "session" | "last3") {
    if (mode === "session") return null; // all history
    if (mode === "last3") return Math.max(0, messages.length - 6); // last 3 exchanges = 6 messages
    return Math.max(0, messages.length - 4); // realtime = last 2 exchanges = 4 messages
  }

  async function handleSupervise(mode: "realtime" | "session" | "last3") {
    setSupervisionMode(mode);
    setSupervisionPanelOpen(true);
    setSupervisionContent("");
    setSupervisionLoading(true);

    // Build the history to send
    const startFrom = getHistorySlice(mode);
    const historyToSend = startFrom !== null ? messages.slice(startFrom) : messages;

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/sessions/${sessionId}/supervise-preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ approach, mode, history: historyToSend }),
      });
      if (!res.ok) throw new Error("Erro na supervisão");
      const reader = res.body?.getReader();
      if (!reader) throw new Error("Sem stream");
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop() ?? "";
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const payload = JSON.parse(line.slice(6).trim());
            if (payload.type === "token") setSupervisionContent((c) => c + payload.content);
            if (payload.type === "done") { reader.cancel(); break; }
          } catch { /* ignora */ }
        }
      }
    } catch {
      setSupervisionContent("Erro ao gerar supervisão. Tente novamente.");
    } finally {
      setSupervisionLoading(false);
    }
  }

  function handleEnd() {
    const params = new URLSearchParams({
      nome: session?.nome ?? "",
      approach,
    });
    router.push(`/session/${sessionId}/supervision?${params}`);
  }

  if (!session) {
    return (
      <div className="min-h-screen flex items-center justify-center text-sm font-mono"
        style={{ background: "var(--bg)", color: "var(--text-faint)" }}>
        carregando sessão...
      </div>
    );
  }

  const nivel = NIVEL[session.nivel as keyof typeof NIVEL] ?? NIVEL.iniciante;
  const turnCount = messages.filter(m => m.role === "user").length;

  return (
    <div className="flex flex-col h-screen" style={{ background: "var(--bg)" }}>

      {/* Topbar */}
      <header className="h-11 px-5 flex items-center gap-3 shrink-0"
        style={{ background: "var(--nav-bg)", color: "var(--nav-text)" }}>
        <button onClick={() => router.push("/")}
          className="font-bold text-sm tracking-tight hover:opacity-80 transition-opacity">
          psysim
        </button>
        <span style={{ background: "var(--surface)", width: 1, opacity: 0.15 }} className="h-4" />
        <span className="text-sm" style={{ color: "rgba(250,250,247,0.7)" }}>{session.nome}</span>
        <span className="text-xs font-mono px-1.5 py-0.5 rounded"
          style={{ background: nivel.bg, color: nivel.fg }}>
          {session.nivel}
        </span>
        <span className="text-xs font-mono" style={{ color: "rgba(250,250,247,0.35)" }}>
          {turnCount}t
        </span>

        <div className="ml-auto flex items-center gap-1">
          {(showTimer || timer) && (
            <>
              <button onClick={handleToggleTimer}
                className="text-xs font-mono px-2.5 h-7 rounded transition-colors"
                style={{
                  background: showTimer ? "rgba(255,255,255,0.15)" : "transparent",
                  color: showTimer ? "var(--nav-text)" : "rgba(250,250,247,0.5)",
                }}>
                ⏱ {showTimer && timer ? timer.elapsed_str : ""}
              </button>
              {showTimer && timer && (
                <button onClick={handleToggleTimer}
                  className="text-xs font-mono px-2.5 h-7 rounded transition-colors"
                  style={{ background: "rgba(255,255,255,0.1)", color: "var(--nav-text)" }}>
                  {timer.is_paused ? "▶" : "⏸"}
                </button>
              )}
            </>
          )}

          {supervisionPanelOpen ? (
            <>
              {/* Mode selector inline in navbar */}
              <div className="flex items-center gap-1">
                <span className="text-xs font-mono" style={{ color: "rgba(250,250,247,0.4)" }}>supervisão:</span>
                <button onClick={() => handleSupervise("realtime")}
                  className="text-xs font-mono px-2 h-7 rounded transition-colors"
                  style={{ background: "rgba(255,255,255,0.12)", color: "var(--nav-text)" }}>
                  🎯tempo real
                </button>
                <button onClick={() => handleSupervise("session")}
                  className="text-xs font-mono px-2 h-7 rounded transition-colors"
                  style={{ background: "rgba(255,255,255,0.12)", color: "var(--nav-text)" }}>
                  📋sessão
                </button>
                <button onClick={() => handleSupervise("last3")}
                  className="text-xs font-mono px-2 h-7 rounded transition-colors"
                  style={{ background: "rgba(255,255,255,0.12)", color: "var(--nav-text)" }}>
                  ⏪recente
                </button>
              </div>
              <button onClick={() => setSupervisionPanelOpen(false)}
                className="text-xs font-mono px-2 h-7 rounded transition-colors"
                style={{ color: "rgba(250,250,247,0.5)" }}>
                ✕
              </button>
            </>
          ) : (
            <button onClick={() => setSupervisionPanelOpen(true)}
              className="text-xs font-mono px-2.5 h-7 rounded transition-colors hover:bg-white/10"
              style={{ color: "rgba(250,250,247,0.5)" }}>
              🎓 supervisão
            </button>
          )}

          <div className="w-px h-4 mx-1" style={{ background: "rgba(255,255,255,0.12)" }} />
          <button onClick={handleEnd}
            className="text-xs font-mono px-3 h-7 rounded border transition-colors hover:bg-white/10"
            style={{ borderColor: "rgba(255,255,255,0.2)", color: "rgba(250,250,247,0.7)" }}>
            Encerrar
          </button>
        </div>
      </header>

      {/* Timer bar */}
      {showTimer && (
        <div className="h-8 px-5 flex items-center gap-5 shrink-0 text-xs font-mono"
          style={{ background: "#111", color: "rgba(250,250,247,0.5)", borderBottom: "1px solid #2a2a2a" }}>
          {timer ? (
            <>
              <span>Decorrido <strong style={{ color: "var(--nav-text)" }}>{timer.elapsed_str}</strong></span>
              {timer.remaining_str && (
                <span>Restam <strong style={{ color: timer.expired ? "var(--red-fg)" : "var(--nav-text)" }}>
                  {timer.remaining_str}
                </strong></span>
              )}
              {timer.is_paused && <span style={{ color: "var(--yellow-fg)" }}>⏸ pausado</span>}
            </>
          ) : (
            <span style={{ color: "rgba(250,250,247,0.4)" }}>timer não configurado</span>
          )}
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">

        {/* Chat */}
        <div className="flex flex-col flex-1 overflow-hidden">
          <div className="flex-1 overflow-y-auto px-6 py-6 flex flex-col gap-4">
            {messages.length === 0 && (
              <p className="text-center text-sm font-mono mt-20"
                style={{ color: "var(--text-faint)" }}>
                Cumprimente {session.nome} para começar.
              </p>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`flex flex-col gap-1 ${msg.role === "user" ? "items-end" : "items-start"}`}>
                <span className="text-xs font-mono px-1" style={{ color: "var(--text-faint)" }}>
                  {msg.role === "user" ? "você" : session.nome.toLowerCase()}
                </span>
                <div className={`max-w-[70%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                  msg.role === "user" ? "rounded-br-sm" : "rounded-bl-sm"
                } ${msg.pending ? "opacity-50" : ""}`}
                  style={{
                    background: msg.role === "user"
                      ? "var(--bubble-therapist)"
                      : "var(--bubble-patient)",
                    color: "var(--text)",
                    border: "1px solid var(--border)",
                  }}>
                  {msg.content || (msg.pending
                    ? <span className="inline-flex gap-1 text-base" style={{ color: "var(--text-faint)" }}>
                        <span className="animate-bounce [animation-delay:0ms]">·</span>
                        <span className="animate-bounce [animation-delay:120ms]">·</span>
                        <span className="animate-bounce [animation-delay:240ms]">·</span>
                      </span>
                    : "")}
                </div>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="shrink-0 px-5 py-3"
            style={{ background: "var(--surface)", borderTop: "1px solid var(--border)" }}>
            <div className="flex gap-2">
              <input
                className="flex-1 rounded-lg px-4 py-2.5 text-sm outline-none transition-all"
                style={{
                  background: "var(--bg)",
                  border: "1px solid var(--border)",
                  color: "var(--text)",
                }}
                placeholder="Sua fala terapêutica..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
                disabled={streaming}
                autoFocus
              />
              <button
                onClick={handleSend}
                disabled={streaming || !input.trim()}
                className="px-5 py-2.5 rounded-lg text-sm font-medium transition-opacity disabled:opacity-30"
                style={{ background: "var(--nav-bg)", color: "var(--nav-text)" }}>
                →
              </button>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <aside className="w-60 shrink-0 hidden lg:flex flex-col"
          style={{ background: "var(--surface)", borderLeft: "1px solid var(--border)" }}>

          {/* Ficha */}
          <div className="px-4 py-3" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
            <p className="label mb-3">Ficha</p>
            <p className="font-semibold text-sm" style={{ color: "var(--text)" }}>{session.nome}</p>
            <p className="text-xs font-mono mt-0.5" style={{ color: "var(--text-faint)" }}>{session.nivel}</p>
          </div>

          {/* Abordagens */}
          <div className="px-4 py-3" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
            <p className="label mb-2">Abordagens</p>
            <div className="flex flex-wrap gap-1">
              {session.approaches.map((a) => (
                <span key={a} className="text-xs font-mono px-1.5 py-0.5 rounded"
                  style={{ background: "var(--bg)", border: "1px solid var(--border)", color: "var(--text-muted)" }}>
                  {a}
                </span>
              ))}
            </div>
          </div>

          {/* Abordagem */}
          <div className="px-4 py-3" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
            <p className="label mb-2">Abordagem</p>
            <div className="flex flex-col gap-1">
              {session.approaches.map((a) => (
                <button key={a} onClick={() => setApproach(a)}
                  className="text-left text-xs font-mono px-2 py-1.5 rounded transition-colors"
                  style={{
                    background: approach === a ? "var(--nav-bg)" : "transparent",
                    color: approach === a ? "var(--nav-text)" : "var(--text-muted)",
                  }}>
                  {approach === a ? "● " : "○ "}{a}
                </button>
              ))}
            </div>
          </div>

          {/* Notas pessoais */}
          <div className="px-4 py-3 flex flex-col flex-1">
            <p className="label mb-2">Notas</p>
            <textarea
              className="flex-1 text-xs resize-none rounded-lg p-2.5 outline-none min-h-[80px]"
              style={{
                background: "var(--bg)",
                border: "1px solid var(--border)",
                color: "var(--text)",
                fontFamily: "var(--font-sans)",
              }}
              placeholder="Anote observações durante a sessão..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>
        </aside>

        {/* Supervision panel — right drawer */}
        {supervisionPanelOpen && (
          <div className="w-80 shrink-0 flex flex-col overflow-hidden"
            style={{ background: "var(--surface)", borderLeft: "1px solid var(--border)" }}>

            {/* Header */}
            <div className="px-4 py-3 flex items-center justify-between"
              style={{ borderBottom: "1px solid var(--border-subtle)" }}>
              <p className="label">Supervisor IA</p>
              <button onClick={() => setSupervisionPanelOpen(false)}
                className="text-xs font-mono text-faint hover:text-default transition-colors">✕</button>
            </div>

            {/* Mode buttons */}
            {!supervisionContent && !supervisionLoading && (
              <div className="px-4 py-4">
                <p className="text-xs font-mono mb-1" style={{ color: "var(--text-faint)" }}>
                  Escolha um modo na barra superior 🎓
                </p>
                <p className="text-xs font-mono mt-2" style={{ color: "var(--text-faint)" }}>
                  Abordagem: <span className="font-bold">{approach}</span>
                </p>
              </div>
            )}

            {/* Loading state */}
            {supervisionLoading && (
              <div className="flex-1 flex items-center justify-center">
                <span className="text-xs font-mono animate-pulse" style={{ color: "var(--text-faint)" }}>
                  gerando supervisão...
                </span>
              </div>
            )}

            {/* Content */}
            {supervisionContent && !supervisionLoading && (
              <div className="flex-1 overflow-y-auto px-4 py-3">
                <div className="prose prose-xs max-w-none"
                  style={{ fontSize: "0.8rem", lineHeight: "1.5" }}>
                  <div style={{ color: "var(--text)" }}>{supervisionContent}</div>
                </div>
                <button onClick={() => { setSupervisionContent(""); setSupervisionMode(null); }}
                  className="mt-3 text-xs font-mono px-3 py-2 rounded-lg border transition-colors"
                  style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}>
                  Nova supervisão
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
