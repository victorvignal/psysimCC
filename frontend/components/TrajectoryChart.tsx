"use client";

import { useEffect, useState } from "react";
import { getTrajectory, type TrajectoryEntry } from "@/lib/api";

function scoreBg(score: number): string {
  if (score <= 2) return "var(--red-bg)";
  if (score === 3) return "var(--yellow-bg)";
  return "var(--green-bg)";
}

function scoreFg(score: number): string {
  if (score <= 2) return "var(--red-fg)";
  if (score === 3) return "var(--yellow-fg)";
  return "var(--green-fg)";
}

export default function TrajectoryChart() {
  const [entries, setEntries] = useState<TrajectoryEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTrajectory()
      .then(setEntries)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <p className="text-xs font-mono" style={{ color: "var(--text-faint)" }}>
        carregando trajetória...
      </p>
    );
  }

  if (entries.length === 0) return null;

  const allDims = Array.from(
    new Set(entries.flatMap((e) => e.rubric_scores.map((r) => r.nome)))
  );

  const recent = entries.slice(-8);
  const offset = entries.length - recent.length;

  return (
    <div className="rounded-xl overflow-hidden"
      style={{ border: "1px solid var(--border)", background: "var(--surface)" }}>
      <div className="px-5 py-3" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
        <span className="label">Trajetória de competências</span>
        <span className="text-xs font-mono ml-2" style={{ color: "var(--text-faint)" }}>
          últimas {recent.length} sessões
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
              <th className="px-4 py-2 text-left font-mono font-normal"
                style={{ color: "var(--text-faint)", minWidth: 210 }}>
                Dimensão
              </th>
              {recent.map((e, i) => (
                <th key={e.id} className="px-2 py-2 text-center font-mono font-normal"
                  style={{ color: "var(--text-faint)", minWidth: 52 }}>
                  S{offset + i + 1}
                  <br />
                  <span style={{ fontSize: "0.6rem", opacity: 0.7 }}>
                    {e.approach.slice(0, 4)}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {allDims.map((dim) => (
              <tr key={dim} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                <td className="px-4 py-2 font-mono text-xs"
                  style={{ color: "var(--text-muted)" }}>
                  {dim}
                </td>
                {recent.map((entry) => {
                  const r = entry.rubric_scores.find((r) => r.nome === dim);
                  if (!r) return (
                    <td key={entry.id} className="px-2 py-2 text-center">
                      <span style={{ color: "var(--text-faint)" }}>—</span>
                    </td>
                  );
                  return (
                    <td key={entry.id} className="px-2 py-2 text-center">
                      <span
                        className="inline-flex items-center justify-center w-7 h-7 rounded text-xs font-mono font-bold"
                        style={{ background: scoreBg(r.score), color: scoreFg(r.score) }}
                        title={r.anchor || undefined}
                      >
                        {r.score}
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
