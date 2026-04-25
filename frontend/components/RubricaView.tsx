"use client";

import type { DimensaoRubrica } from "@/lib/api";

function scoreColor(score: number): { bg: string; fg: string } {
  if (score <= 2) return { bg: "var(--red-bg)",    fg: "var(--red-fg)" };
  if (score === 3) return { bg: "var(--yellow-bg)", fg: "var(--yellow-fg)" };
  return              { bg: "var(--green-bg)",   fg: "var(--green-fg)" };
}

function ScoreDots({ score }: { score: number }) {
  const { fg } = scoreColor(score);
  return (
    <div className="flex gap-1">
      {Array.from({ length: 5 }, (_, i) => (
        <div key={i} className="w-5 h-5 rounded-sm border-2 transition-colors"
          style={{
            background: i < score ? fg : "transparent",
            borderColor: i < score ? fg : "var(--border)",
          }} />
      ))}
    </div>
  );
}

export default function RubricaView({
  dimensoes,
  approach,
}: {
  dimensoes: DimensaoRubrica[];
  approach: string;
}) {
  const total = dimensoes.reduce((s, d) => s + d.score, 0);
  const media = dimensoes.length ? (total / dimensoes.length).toFixed(1) : "—";

  return (
    <div className="rounded-xl overflow-hidden"
      style={{ border: "1px solid var(--border)", background: "var(--surface)" }}>

      {/* Header */}
      <div className="px-5 py-3 flex items-center justify-between"
        style={{ borderBottom: "1px solid var(--border-subtle)" }}>
        <div className="flex items-center gap-2">
          <span className="label">Rubrica de competências</span>
          <span className="text-xs font-mono px-2 py-0.5 rounded"
            style={{ background: "var(--green-bg)", color: "var(--green-fg)" }}>
            {approach}
          </span>
        </div>
        <div className="text-right">
          <span className="text-xs font-mono" style={{ color: "var(--text-faint)" }}>média </span>
          <span className="text-sm font-bold font-mono" style={{ color: "var(--text)" }}>{media}</span>
          <span className="text-xs font-mono" style={{ color: "var(--text-faint)" }}>/5</span>
        </div>
      </div>

      {/* Dimensões */}
      <div className="divide-y" style={{ borderColor: "var(--border-subtle)" }}>
        {dimensoes.map((d) => {
          const { bg, fg } = scoreColor(d.score);
          return (
            <div key={d.nome} className="px-5 py-4">
              <div className="flex items-start justify-between gap-4 mb-2">
                <span className="text-sm font-medium" style={{ color: "var(--text)" }}>
                  {d.nome}
                </span>
                <div className="flex items-center gap-2 shrink-0">
                  <ScoreDots score={d.score} />
                  <span className="text-xs font-mono font-bold w-6 text-right"
                    style={{ color: fg }}>
                    {d.score}/5
                  </span>
                </div>
              </div>
              {d.justificativa && (
                <p className="text-xs leading-relaxed pl-0"
                  style={{ color: "var(--text-muted)" }}>
                  {d.justificativa}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
