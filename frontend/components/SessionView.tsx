"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  getSession,
  toggleTimer,
  streamMessage,
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
  const [notes, setNotes] = useState("");
  const [approach, setApproach] = useState("TCC");
  const bottomRef = useRef<HTMLDivElement>(null);
  const cancelRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    getSession(sessionId).then((s) => {
      setSession(s);
      setTimer(s.timer);
    });
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

    cancelRef.current = streamMessage(
      sessionId,
      text,
      (token) => {
        setMessages((m) => {
          const last = m[m.length - 1];
          if (!last || last.role !== "assistant") return m;
          return [...m.slice(0, -1), { ...last, content: last.content + token }];
        });
      },
      () => {
        setMessages((m) => {
          const last = m[m.length - 1];
          if (!last) return m;
          return [...m.slice(0, -1), { ...last, pending: false }];
        });
        setStreaming(false);
      }
    );
  }

  async function handleToggleTimer() {
    const result = await toggleTimer(sessionId);
    setTimer((t) => t ? { ...t, is_paused: result.is_paused, elapsed_str: result.elapsed_str } : t);
  }

  function handleEnd() {
    cancelRef.current?.();
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
        <span className="font-bold text-sm tracking-tight">psysim</span>
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
          {timer && (
            <>
              <button onClick={() => setShowTimer(v => !v)}
                className="text-xs font-mono px-2.5 h-7 rounded transition-colors"
                style={{
                  background: showTimer ? "rgba(255,255,255,0.15)" : "transparent",
                  color: showTimer ? "var(--nav-text)" : "rgba(250,250,247,0.5)",
                }}>
                {showTimer ? `⏱ ${timer.elapsed_str}` : "⏱"}
              </button>
              {showTimer && (
                <button onClick={handleToggleTimer}
                  className="text-xs font-mono px-2.5 h-7 rounded transition-colors"
                  style={{ background: "rgba(255,255,255,0.1)", color: "var(--nav-text)" }}>
                  {timer.is_paused ? "▶" : "⏸"}
                </button>
              )}
            </>
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
      {timer && showTimer && (
        <div className="h-8 px-5 flex items-center gap-5 shrink-0 text-xs font-mono"
          style={{ background: "#111", color: "rgba(250,250,247,0.5)", borderBottom: "1px solid #2a2a2a" }}>
          <span>Decorrido <strong style={{ color: "var(--nav-text)" }}>{timer.elapsed_str}</strong></span>
          {timer.remaining_str && (
            <span>Restam <strong style={{ color: timer.expired ? "var(--red-fg)" : "var(--nav-text)" }}>
              {timer.remaining_str}
            </strong></span>
          )}
          {timer.is_paused && <span style={{ color: "var(--yellow-fg)" }}>⏸ pausado</span>}
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
      </div>
    </div>
  );
}
