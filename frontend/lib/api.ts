const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface FichaInfo {
  id: string;
  nome: string;
  idade: number;
  genero: string;
  ocupacao: string;
  queixa: string;
  nivel: "iniciante" | "intermediario" | "avancado";
}

export interface SessionInfo {
  session_id: string;
  ficha: { id: string; nome: string; nivel: string };
  timer_minutes: number;
}

export interface TimerInfo {
  elapsed_str: string;
  remaining_str: string | null;
  is_paused: boolean;
  expired: boolean;
  duration_minutes: number;
}

export interface SessionState {
  session_id: string;
  ficha_id: string;
  nome: string;
  nivel: string;
  turn_count: number;
  timer: TimerInfo | null;
  approaches: string[];
}

export async function listFichas(): Promise<FichaInfo[]> {
  const res = await fetch(`${BASE}/api/fichas`);
  if (!res.ok) throw new Error("Erro ao carregar fichas");
  return res.json();
}

export async function startSession(
  fichaId: string,
  timerMinutes = 0
): Promise<SessionInfo> {
  const res = await fetch(`${BASE}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ficha_id: fichaId, timer_minutes: timerMinutes }),
  });
  if (!res.ok) throw new Error("Erro ao iniciar sessão");
  return res.json();
}

export async function getSession(sessionId: string): Promise<SessionState> {
  const res = await fetch(`${BASE}/api/sessions/${sessionId}`);
  if (!res.ok) throw new Error("Sessão não encontrada");
  return res.json();
}

export async function endSession(sessionId: string): Promise<void> {
  await fetch(`${BASE}/api/sessions/${sessionId}`, { method: "DELETE" });
}

export async function toggleTimer(
  sessionId: string
): Promise<{ is_paused: boolean; elapsed_str: string }> {
  const res = await fetch(`${BASE}/api/sessions/${sessionId}/timer/toggle`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Erro ao alternar timer");
  return res.json();
}

export interface DimensaoRubrica {
  nome: string;
  score: number;
  justificativa: string;
}

export interface Rubrica {
  approach: string;
  dimensoes: DimensaoRubrica[];
}

export interface DashboardStats {
  sessions: number;
  minutes: number;
  feedbacks: number;
  patients: number;
}

export interface Dashboard {
  stats: DashboardStats;
  recent_sessions: Array<{
    id: string;
    ficha_id: string;
    created_at: string;
    duration_seconds: number;
  }>;
  progress: Record<string, Record<string, number[]>>;
}

export async function getDashboard(): Promise<Dashboard> {
  const res = await fetch(`${BASE}/api/dashboard`);
  if (!res.ok) throw new Error("Erro ao carregar dashboard");
  return res.json();
}

export async function getRubric(
  sessionId: string,
  approach: string
): Promise<Rubrica> {
  const res = await fetch(`${BASE}/api/sessions/${sessionId}/rubric`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approach }),
  });
  if (!res.ok) throw new Error("Erro ao gerar rubrica");
  return res.json();
}

function makeStreamer(url: string, body: object, onToken: (t: string) => void, onDone: () => void): () => void {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) return;

      const reader = res.body.getReader();
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
            if (payload.type === "token") onToken(payload.content);
            if (payload.type === "done") { reader.cancel(); return; }
          } catch { /* ignora linhas malformadas */ }
        }
      }
    } catch (e) {
      if (e instanceof Error && e.name === "AbortError") return;
    } finally {
      onDone();
    }
  })();

  return () => controller.abort();
}

export function streamMessage(
  sessionId: string,
  content: string,
  onToken: (t: string) => void,
  onDone: () => void
): () => void {
  return makeStreamer(
    `${BASE}/api/sessions/${sessionId}/message`,
    { content },
    onToken,
    onDone
  );
}

export function streamSupervision(
  sessionId: string,
  approach: string,
  onToken: (t: string) => void,
  onDone: () => void
): () => void {
  return makeStreamer(
    `${BASE}/api/sessions/${sessionId}/supervise`,
    { approach },
    onToken,
    onDone
  );
}
