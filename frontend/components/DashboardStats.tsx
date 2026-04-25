import type { Dashboard } from "@/lib/api";

const RUBRICA_DIMS = [
  "Empatia e validação",
  "Formulação de caso",
  "Técnica de entrevista",
  "Manejo de resistência",
  "Aliança terapêutica",
  "Planejamento terapêutico",
];

function avg(scores: number[]): number {
  if (!scores.length) return 0;
  return scores.reduce((a, b) => a + b, 0) / scores.length;
}

function scoreColor(value: number): string {
  if (value === 0) return "var(--border)";
  if (value < 2.5) return "var(--red-fg)";
  if (value < 3.5) return "var(--yellow-fg)";
  return "var(--green-fg)";
}

function ProgressBar({ value, max = 5 }: { value: number; max?: number }) {
  const pct = Math.round((value / max) * 100);
  return (
    <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "var(--border)" }}>
      <div className="h-full rounded-full transition-all"
        style={{ width: `${pct}%`, background: scoreColor(value) }} />
    </div>
  );
}

const STAT_LABELS = [
  { key: "sessions", label: "sessões" },
  { key: "minutes", label: "min de prática" },
  { key: "feedbacks", label: "supervisões" },
  { key: "patients", label: "pacientes" },
] as const;

export default function DashboardStats({ dashboard }: { dashboard: Dashboard }) {
  const { stats, progress } = dashboard;

  // Agrega progresso de todas as fichas
  const allProgress: Record<string, number[]> = {};
  for (const fichaProgress of Object.values(progress)) {
    for (const [dim, scores] of Object.entries(fichaProgress)) {
      allProgress[dim] = [...(allProgress[dim] || []), ...scores];
    }
  }

  const hasProgress = Object.keys(allProgress).length > 0;

  return (
    <div className="flex flex-col lg:flex-row gap-5">

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-2 gap-3 lg:w-72 shrink-0">
        {STAT_LABELS.map(({ key, label }) => (
          <div key={key} className="rounded-xl px-4 py-4"
            style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
            <div className="text-2xl font-bold font-mono" style={{ color: "var(--text)" }}>
              {stats[key]}
            </div>
            <div className="text-xs font-mono mt-0.5" style={{ color: "var(--text-faint)" }}>
              {label}
            </div>
          </div>
        ))}
      </div>

      {/* Progresso por competência */}
      <div className="flex-1 rounded-xl px-5 py-4"
        style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
        <p className="label mb-4">Progresso por competência</p>

        {!hasProgress ? (
          <p className="text-xs font-mono" style={{ color: "var(--text-faint)" }}>
            Complete uma supervisão para ver seu progresso.
          </p>
        ) : (
          <div className="flex flex-col gap-3">
            {RUBRICA_DIMS.map((dim) => {
              const scores = allProgress[dim] || [];
              const media = avg(scores);
              return (
                <div key={dim}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs" style={{ color: "var(--text-muted)" }}>{dim}</span>
                    <span className="text-xs font-mono font-bold"
                      style={{ color: media ? scoreColor(media) : "var(--text-faint)" }}>
                      {media ? media.toFixed(1) : "—"}
                    </span>
                  </div>
                  <ProgressBar value={media} />
                </div>
              );
            })}
            <p className="text-xs font-mono mt-1" style={{ color: "var(--text-faint)" }}>
              baseado em {stats.feedbacks} {stats.feedbacks === 1 ? "supervisão" : "supervisões"}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
