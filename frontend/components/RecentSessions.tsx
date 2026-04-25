"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { deleteSession } from "@/lib/api";

interface RecentSession {
  id: string;
  ficha_id: string;
  ficha_nome: string;
  created_at: string;
  duration_seconds: number;
}

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m}m` : `${s}s`;
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

interface DeleteButtonProps {
  sessionId: string;
}

function DeleteButton({ sessionId }: DeleteButtonProps) {
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function handleDelete() {
    if (!confirming) { setConfirming(true); return; }
    setDeleting(true);
    try {
      await deleteSession(sessionId);
      window.location.reload();
    } catch {
      setDeleting(false);
      setConfirming(false);
    }
  }

  if (confirming) {
    return (
      <div className="flex items-center gap-1 shrink-0">
        <span className="text-xs font-mono" style={{ color: "var(--red-fg)" }}>deletar?</span>
        <button onClick={handleDelete} disabled={deleting}
          className="text-xs font-mono px-2 py-1 rounded disabled:opacity-40"
          style={{ background: "var(--red-fg)", color: "white" }}>
          {deleting ? "..." : "sim"}
        </button>
        <button onClick={() => setConfirming(false)}
          className="text-xs font-mono px-2 py-1 rounded"
          style={{ background: "var(--border)", color: "var(--text-muted)" }}>
          não
        </button>
      </div>
    );
  }

  return (
    <button onClick={() => setConfirming(true)}
      className="text-xs font-mono px-2 py-1 rounded opacity-0 hover:opacity-100 transition-opacity shrink-0"
      style={{ background: "var(--bg)", color: "var(--text-faint)", border: "1px solid var(--border)" }}
      title="Deletar sessão">
      🗑
    </button>
  );
}

export default function RecentSessions({ sessions }: { sessions: RecentSession[] }) {
  const router = useRouter();

  return (
    <div>
      <h2 className="text-lg font-bold mb-4" style={{ color: "var(--text)" }}>
        Sessões recentes
      </h2>
      <div className="rounded-xl overflow-hidden"
        style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
        {sessions.map((s, i) => (
          <div key={s.id}
            className="flex items-center gap-3 px-5 py-4 group cursor-pointer hover:bg-black/[0.03] transition-colors"
            style={{ borderBottom: i < sessions.length - 1 ? "1px solid var(--border-subtle)" : undefined }}
            onClick={() => router.push(`/session/${s.id}`)}>
            {/* Avatar circle */}
            <div className="w-9 h-9 rounded-full shrink-0 flex items-center justify-center text-sm font-bold"
              style={{ background: "var(--green-bg)", color: "var(--green-fg)" }}>
              {s.ficha_nome?.[0] ?? "?"}
            </div>
            {/* Info */}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold truncate" style={{ color: "var(--text)" }}>
                {s.ficha_nome}
              </p>
              <p className="text-xs font-mono mt-0.5" style={{ color: "var(--text-faint)" }}>
                {formatDate(s.created_at)} · {formatDuration(s.duration_seconds)}
              </p>
            </div>
            {/* Delete button */}
            <div className="opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={e => e.stopPropagation()}>
              <DeleteButton sessionId={s.id} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}