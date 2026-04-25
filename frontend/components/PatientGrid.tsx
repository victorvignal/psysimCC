"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { startSession, type FichaInfo } from "@/lib/api";

const NIVEL = {
  iniciante:     { bg: "var(--green-bg)",  fg: "var(--green-fg)",  label: "Iniciante" },
  intermediario: { bg: "var(--yellow-bg)", fg: "var(--yellow-fg)", label: "Intermediário" },
  avancado:      { bg: "var(--red-bg)",    fg: "var(--red-fg)",    label: "Avançado" },
} as const;

export default function PatientGrid({ fichas }: { fichas: FichaInfo[] }) {
  const router = useRouter();
  const [loading, setLoading] = useState<string | null>(null);

  async function handleStart(ficha: FichaInfo) {
    setLoading(ficha.id);
    try {
      const session = await startSession(ficha.id);
      router.push(`/session/${session.session_id}`);
    } catch {
      setLoading(null);
    }
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {fichas.map((f) => {
        const nivel = NIVEL[f.nivel as keyof typeof NIVEL] ?? NIVEL.iniciante;
        return (
          <div key={f.id} className="flex flex-col rounded-xl overflow-hidden"
            style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>

            {/* Header colorido por nível */}
            <div className="px-5 pt-4 pb-3 flex items-start justify-between gap-3"
              style={{ background: nivel.bg, borderBottom: `1px solid ${nivel.bg}` }}>
              <div>
                <div className="text-lg font-bold" style={{ color: "var(--text)" }}>
                  {f.nome}, {f.idade}
                </div>
                <div className="text-xs mt-0.5 font-mono" style={{ color: "var(--text-muted)" }}>
                  {f.ocupacao}
                </div>
              </div>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded shrink-0 mt-0.5"
                style={{ background: "rgba(255,255,255,0.6)", color: nivel.fg }}>
                {nivel.label}
              </span>
            </div>

            {/* Queixa */}
            <div className="px-5 py-4 flex-1">
              <p className="text-xs font-mono mb-1" style={{ color: "var(--text-faint)" }}>
                QUEIXA
              </p>
              <p className="text-sm leading-relaxed line-clamp-3 italic"
                style={{ color: "var(--text-muted)" }}>
                &ldquo;{f.queixa.replace(/^"|"$/g, "")}&rdquo;
              </p>
            </div>

            {/* Botão */}
            <div className="px-5 pb-5">
              <button
                onClick={() => handleStart(f)}
                disabled={loading !== null}
                className="w-full rounded-lg py-2 text-sm font-medium transition-opacity disabled:opacity-40 disabled:cursor-not-allowed"
                style={{ background: "var(--nav-bg)", color: "var(--nav-text)" }}>
                {loading === f.id ? "Iniciando..." : "Iniciar sessão →"}
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
