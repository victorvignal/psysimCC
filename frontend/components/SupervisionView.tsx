"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";
import { saveSession, getRubric, streamSupervision, type Rubrica } from "@/lib/api";
import RubricaView from "./RubricaView";

const APPROACHES = ["TCC", "Psicodinâmica", "Humanista", "ACT", "Sistêmica", "Integrativa"];

export default function SupervisionView({
  sessionId,
  nome,
  initialApproach,
}: {
  sessionId: string;
  nome: string;
  initialApproach: string;
}) {
  const router = useRouter();
  const [approach, setApproach] = useState(initialApproach || "TCC");
  const [feedback, setFeedback] = useState("");
  const [rubrica, setRubrica] = useState<Rubrica | null>(null);
  const [loadingRubric, setLoadingRubric] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Save session when arriving at supervision page
  useEffect(() => {
    // Session is already saved when user clicked "Encerrar" on SessionView
    // This just cleans up if user navigates away without saving
    return () => { saveSession(sessionId).catch(() => {}); };
  }, [sessionId]);

  async function handleStart() {
    setFeedback("");
    setRubrica(null);
    setDone(false);
    setError(null);
    setStreaming(true);
    setLoadingRubric(true);

    getRubric(sessionId)
      .then((r) => setRubrica(r))
      .catch(() => {})
      .finally(() => setLoadingRubric(false));

    const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    try {
      const { authHeaders } = await import("@/lib/api");
      const res = await fetch(`${BASE}/api/sessions/${sessionId}/supervise`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ approach }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Erro ${res.status}`);
      }

      const reader = res.body?.getReader();
      if (!reader) throw new Error("Sem stream");
      const decoder = new TextDecoder();
      let buf = "";

      while (true) {
        const { done: streamDone, value } = await reader.read();
        if (streamDone) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop() ?? "";
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const payload = JSON.parse(line.slice(6).trim());
            if (payload.type === "token") setFeedback((f) => f + payload.content);
            if (payload.type === "done") { reader.cancel(); return; }
          } catch { /* ignora linhas malformadas */ }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setStreaming(false);
      setDone(true);
    }
  }

  function handleReset() {
    setFeedback("");
    setRubrica(null);
    setDone(false);
  }

  return (
    <div className="min-h-screen" style={{ background: "var(--bg)" }}>

      <nav className="h-11 px-6 flex items-center gap-3"
        style={{ background: "var(--nav-bg)", color: "var(--nav-text)" }}>
        <span className="font-bold text-sm tracking-tight">psysim</span>
        <span className="w-px h-4 opacity-20" style={{ background: "var(--nav-text)" }} />
        <span className="text-sm" style={{ color: "rgba(250,250,247,0.6)" }}>
          Supervisão · {nome}
        </span>
        <button onClick={() => router.push("/")}
          className="ml-auto text-xs font-mono"
          style={{ color: "rgba(250,250,247,0.4)" }}
          onMouseEnter={e => (e.currentTarget.style.color = "var(--nav-text)")}
          onMouseLeave={e => (e.currentTarget.style.color = "rgba(250,250,247,0.4)")}>
          ← voltar
        </button>
      </nav>

      <div className="max-w-4xl mx-auto px-6 py-10">

        <h1 className="text-xl font-bold mb-1" style={{ color: "var(--text)" }}>
          Supervisão pós-sessão
        </h1>
        <p className="text-xs font-mono mb-8" style={{ color: "var(--text-faint)" }}>
          Sessão com {nome}
        </p>

        {/* Seleção de abordagem */}
        {!streaming && !done && (
          <div className="rounded-xl p-6 mb-6"
            style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
            <p className="label mb-3">Abordagem terapêutica</p>
            <div className="flex flex-wrap gap-2 mb-6">
              {APPROACHES.map((a) => (
                <button key={a} onClick={() => setApproach(a)}
                  className="text-xs font-mono px-3 py-1.5 rounded-full border transition-colors"
                  style={{
                    background: approach === a ? "var(--nav-bg)" : "transparent",
                    color: approach === a ? "var(--nav-text)" : "var(--text-muted)",
                    borderColor: approach === a ? "var(--nav-bg)" : "var(--border)",
                  }}>
                  {a}
                </button>
              ))}
            </div>
            <button onClick={handleStart}
              className="w-full rounded-lg py-2.5 text-sm font-medium"
              style={{ background: "var(--nav-bg)", color: "var(--nav-text)" }}>
              Iniciar supervisão →
            </button>
          </div>
        )}

        {/* Erro */}
        {error && (
          <div className="rounded-lg p-4 text-sm mb-6"
            style={{ background: "var(--red-bg)", color: "var(--red-fg)", border: "1px solid var(--red-fg)" }}>
            {error}
            <button onClick={() => { setError(null); setDone(false); setStreaming(false); }}
              className="ml-4 text-xs underline opacity-70">tentar novamente</button>
          </div>
        )}

        {/* Layout rubrica + narrativa */}
        {(streaming || done) && (
          <div className="flex flex-col lg:flex-row gap-6">

            {/* Rubrica — coluna esquerda */}
            <div className="lg:w-80 shrink-0">
              {loadingRubric && !rubrica && (
                <div className="rounded-xl p-5 text-xs font-mono text-center"
                  style={{ background: "var(--surface)", border: "1px solid var(--border)", color: "var(--text-faint)" }}>
                  <span className="animate-pulse">calculando rubrica...</span>
                </div>
              )}
              {rubrica && <RubricaView dimensoes={rubrica.dimensoes} approach={approach} />}
            </div>

            {/* Narrativa — coluna direita */}
            <div className="flex-1 rounded-xl p-6"
              style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>

              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono px-2 py-0.5 rounded"
                    style={{ background: "var(--green-bg)", color: "var(--green-fg)" }}>
                    {approach}
                  </span>
                  <span className="text-xs font-mono" style={{ color: "var(--text-faint)" }}>
                    Supervisor IA
                  </span>
                </div>
                {streaming && (
                  <span className="text-xs font-mono animate-pulse" style={{ color: "var(--text-faint)" }}>
                    analisando...
                  </span>
                )}
              </div>

              <div className="prose prose-sm max-w-none"
                style={{ "--tw-prose-body": "var(--text)", "--tw-prose-headings": "var(--text)" } as React.CSSProperties}>
                <ReactMarkdown>{feedback}</ReactMarkdown>
                {streaming && <span className="animate-pulse" style={{ color: "var(--text-faint)" }}>▌</span>}
              </div>

              {done && (
                <div className="mt-6 pt-5 flex gap-3"
                  style={{ borderTop: "1px solid var(--border-subtle)" }}>
                  <button onClick={handleReset}
                    className="px-4 py-2 rounded-lg text-sm font-mono border transition-colors"
                    style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}>
                    Outra abordagem
                  </button>
                  <button onClick={() => router.push("/")}
                    className="px-4 py-2 rounded-lg text-sm font-mono"
                    style={{ background: "var(--nav-bg)", color: "var(--nav-text)" }}>
                    Nova sessão →
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
