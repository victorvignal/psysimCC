# Auth + Supervisor Preview + Rubrica Avançada — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar autenticação multi-usuário (Supabase Auth), ajustar o supervisor em tempo real para 5 turnos, e implementar rubrica avançada com dimensões por abordagem, âncoras comportamentais e trajetória entre sessões.

**Architecture:** Auth via Supabase Auth (email/password) — JWT verificado no FastAPI com PyJWT, protegido por middleware no Next.js. Rubrica avançada vive em `src/rubrica_data.py` (dict por abordagem) e é consumida pelo `supervisor_agent.py` e pelo `RubricaView`. Trajetória é endpoint `/api/users/me/trajectory` + componente de tabela colorida no dashboard.

**Tech Stack:** Python PyJWT, @supabase/ssr (Next.js middleware + server/browser clients), Supabase Auth (email/password), Next.js App Router middleware, Tailwind v4 (sem chart lib adicional).

---

## Mapa de arquivos

### Criar
- `src/auth.py` — dependência FastAPI `get_current_user(token) -> str (user_id)`
- `src/rubrica_data.py` — `RUBRICA_POR_ABORDAGEM: dict[str, list[dict]]` com âncoras por score
- `frontend/lib/supabase.ts` — browser client (createBrowserClient)
- `frontend/lib/supabase-server.ts` — server client (createServerClient + cookies)
- `frontend/middleware.ts` — redireciona /login se não autenticado
- `frontend/app/login/page.tsx` — página de login
- `frontend/app/register/page.tsx` — página de cadastro
- `frontend/components/AuthForm.tsx` — formulário compartilhado login/registro
- `frontend/components/TrajectoryChart.tsx` — tabela colorida de trajetória entre sessões
- `supabase/migrations/001_add_user_id.sql` — migration (rodar no dashboard Supabase)

### Modificar
- `pyproject.toml` — adicionar PyJWT
- `frontend/package.json` — adicionar @supabase/ssr
- `src/api.py` — adicionar `Depends(get_current_user)` em todos os endpoints, user_id em sessões
- `src/database.py` — `save_session`, `save_supervision`, `get_dashboard` aceitam `user_id`
- `frontend/lib/api.ts` — `setAccessToken()` + headers em todos os fetches
- `frontend/app/page.tsx` — logout no nav + passar token ao API
- `frontend/app/layout.tsx` — AuthProvider (listener de sessão Supabase)
- `frontend/components/SessionView.tsx` — auth header no supervise-preview + "last3" → "last5"
- `frontend/components/RubricaView.tsx` — âncoras por score, dimensões por abordagem
- `frontend/components/DashboardStats.tsx` — adicionar TrajectoryChart
- `frontend/app/session/[sessionId]/supervision/page.tsx` — passar approach para rubrica

---

## FASE 1 — Autenticação

---

### Task 1: Migração do banco — adicionar user_id

**Files:**
- Create: `supabase/migrations/001_add_user_id.sql`

- [ ] **Step 1: Criar arquivo de migração**

```sql
-- supabase/migrations/001_add_user_id.sql
-- Rodar no Supabase Dashboard > SQL Editor

ALTER TABLE sessions      ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES auth.users(id);
ALTER TABLE supervisions  ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES auth.users(id);
ALTER TABLE active_sessions ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES auth.users(id);

-- Índices
CREATE INDEX IF NOT EXISTS sessions_user_id_idx      ON sessions(user_id);
CREATE INDEX IF NOT EXISTS supervisions_user_id_idx  ON supervisions(user_id);
CREATE INDEX IF NOT EXISTS active_sessions_user_id_idx ON active_sessions(user_id);

-- RLS (segurança extra — o backend já filtra por user_id via JWT)
ALTER TABLE sessions       ENABLE ROW LEVEL SECURITY;
ALTER TABLE supervisions   ENABLE ROW LEVEL SECURITY;
ALTER TABLE active_sessions ENABLE ROW LEVEL SECURITY;

-- Policies para o service role (usado pelo backend)
CREATE POLICY "service_role_all_sessions"
  ON sessions FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_all_supervisions"
  ON supervisions FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "service_role_all_active_sessions"
  ON active_sessions FOR ALL TO service_role USING (true) WITH CHECK (true);
```

- [ ] **Step 2: Executar no Supabase**

Abrir https://supabase.com/dashboard/project/hepekrvzmpzzludivhjc/sql/new e colar o SQL acima. Confirmar que todas as colunas existem em Table Editor.

- [ ] **Step 3: Commit**

```bash
cd /c/Users/vigna/.claude/psysim
git add supabase/migrations/001_add_user_id.sql
git commit -m "chore: add user_id columns + RLS to sessions, supervisions, active_sessions"
```

---

### Task 2: Dependência de auth no FastAPI (`src/auth.py`)

**Files:**
- Create: `src/auth.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Adicionar PyJWT ao pyproject.toml**

Em `pyproject.toml`, adicionar na lista `dependencies`:
```
"PyJWT>=2.8.0",
```

Linha inserida após `"sse-starlette>=2.1",`:
```toml
    "sse-starlette>=2.1",
    "PyJWT>=2.8.0",
```

- [ ] **Step 2: Instalar dependência**

```bash
cd /c/Users/vigna/.claude/psysim
uv sync
```

Esperado: PyJWT instalado sem erros.

- [ ] **Step 3: Criar src/auth.py**

```python
import os
import jwt
from fastapi import Depends, HTTPException, Header
from typing import Optional


def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """Extrai e valida o JWT do Supabase. Retorna user_id (sub)."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Não autenticado")

    token = authorization.split(" ", 1)[1].strip()
    secret = (os.getenv("SUPABASE_JWT_SECRET") or "").strip()

    if not secret:
        raise HTTPException(status_code=500, detail="SUPABASE_JWT_SECRET não configurado")

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {e}")

    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token sem sub")
    return user_id
```

- [ ] **Step 4: Smoke test manual**

```bash
cd /c/Users/vigna/.claude/psysim
python -c "from src.auth import get_current_user; print('OK')"
```

Esperado: `OK`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock src/auth.py
git commit -m "feat: add JWT auth dependency (PyJWT + get_current_user)"
```

---

### Task 3: Adicionar auth a todos os endpoints do FastAPI

**Files:**
- Modify: `src/api.py`
- Modify: `src/database.py`

- [ ] **Step 1: Atualizar database.py — user_id em save_session e save_supervision**

Substituir a função `save_session` atual por:

```python
def save_session(
    ficha_id: str,
    turns: list[dict[str, str]],
    duration_seconds: int = 0,
    user_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> str | None:
    client = _get_client()
    if not client:
        return None
    result = (
        client.table("sessions")
        .insert({
            "ficha_id": ficha_id,
            "turns": turns,
            "duration_seconds": duration_seconds,
            "user_id": user_id,
            "metadata": metadata or {},
        })
        .execute()
    )
    return result.data[0]["id"] if result.data else None
```

Substituir `save_supervision` por:

```python
def save_supervision(
    session_id: str | None,
    approach: str,
    feedback: str,
    user_id: str | None = None,
    rubric_scores: list[dict] | None = None,
) -> None:
    client = _get_client()
    if not client:
        return
    client.table("supervisions").insert({
        "session_id": session_id,
        "approach": approach,
        "feedback": feedback,
        "user_id": user_id,
        "rubric_scores": rubric_scores or [],
    }).execute()
```

Substituir `get_dashboard` para filtrar por user_id:

```python
def get_dashboard(user_id: str | None = None) -> dict:
    client = _get_client()
    if not client:
        return _empty_dashboard()

    q_sessions = client.table("sessions").select(
        "id, ficha_id, created_at, duration_seconds"
    ).order("created_at", desc=True)
    if user_id:
        q_sessions = q_sessions.eq("user_id", user_id)
    sessions = q_sessions.execute().data or []

    q_supervisions = client.table("supervisions").select(
        "session_id, approach, rubric_scores, created_at"
    )
    if user_id:
        q_supervisions = q_supervisions.eq("user_id", user_id)
    supervisions = q_supervisions.execute().data or []

    # (resto do corpo permanece igual)
    from src.ficha_loader import load_ficha
    from pathlib import Path
    fichas_dir = Path(__file__).parent.parent / "fichas" / "validated"
    ficha_nomes: dict[str, str] = {}
    try:
        for path in fichas_dir.glob("*.yaml"):
            try:
                f = load_ficha(path)
                ficha_nomes[f.id] = f.apresentacao.nome_ficticio
            except Exception:
                continue
    except Exception:
        pass

    total_sessions = len(sessions)
    total_minutes = sum(s.get("duration_seconds", 0) for s in sessions) // 60
    total_feedbacks = len(supervisions)
    patients = len({s["ficha_id"] for s in sessions if s.get("ficha_id")})

    progress: dict[str, dict[str, list[int]]] = {}
    for sup in supervisions:
        scores = sup.get("rubric_scores") or []
        if not scores:
            continue
        session = next((s for s in sessions if s["id"] == sup.get("session_id")), None)
        ficha_id = session["ficha_id"] if session else "desconhecido"
        if ficha_id not in progress:
            progress[ficha_id] = {}
        for d in scores:
            nome = d.get("nome", "")
            if nome:
                progress[ficha_id].setdefault(nome, []).append(d.get("score", 0))

    recent = []
    for s in sessions[:5]:
        recent.append({
            "id": s["id"],
            "ficha_id": s["ficha_id"],
            "ficha_nome": ficha_nomes.get(s["ficha_id"], s["ficha_id"]),
            "created_at": s["created_at"],
            "duration_seconds": s.get("duration_seconds", 0),
        })

    return {
        "stats": {
            "sessions": total_sessions,
            "minutes": total_minutes,
            "feedbacks": total_feedbacks,
            "patients": patients,
        },
        "recent_sessions": recent,
        "progress": progress,
    }
```

Adicionar função para trajetória:

```python
def get_trajectory(user_id: str) -> list[dict]:
    """Retorna supervisões com rubric_scores ordenadas por data para o user_id."""
    client = _get_client()
    if not client:
        return []
    result = (
        client.table("supervisions")
        .select("id, session_id, approach, rubric_scores, created_at")
        .eq("user_id", user_id)
        .order("created_at")
        .execute()
    )
    return result.data or []
```

- [ ] **Step 2: Atualizar api.py — importar auth e proteger endpoints**

No topo de `src/api.py`, adicionar import:

```python
from src.auth import get_current_user
```

Adicionar `user_id` ao `SessionState`:

```python
@dataclass
class SessionState:
    ficha: Ficha
    agent: PatientAgent
    timer: SessionTimer | None = None
    approach: str = "TCC"
    last_supervision: str = ""
    user_id: str = ""
```

Atualizar `_persist_session` para incluir user_id:

```python
def _persist_session(session_id: str, state: SessionState) -> None:
    from src.database import _get_client
    client = _get_client()
    if not client:
        return
    try:
        client.table("active_sessions").upsert({
            "id": session_id,
            "ficha_id": state.ficha.id,
            "history": state.agent.history,
            "timer_minutes": state.timer.duration_minutes if state.timer else 0,
            "elapsed_seconds": int(state.timer.elapsed_seconds) if state.timer else 0,
            "approach": state.approach,
            "user_id": state.user_id,
            "updated_at": "now()",
        }).execute()
    except Exception:
        pass
```

Atualizar `start_session` para exigir auth:

```python
@app.post("/api/sessions")
def start_session(
    req: StartSessionRequest,
    user_id: str = Depends(get_current_user),
) -> dict:
    path = _FICHAS_DIR / f"{req.ficha_id}.yaml"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Ficha não encontrada")

    ficha = load_ficha(path)
    timer = SessionTimer(req.timer_minutes) if req.timer_minutes > 0 else None
    session_id = str(uuid.uuid4())

    state = SessionState(ficha=ficha, agent=PatientAgent(ficha), timer=timer, user_id=user_id)
    _sessions[session_id] = state
    _persist_session(session_id, state)
    return {
        "session_id": session_id,
        "ficha": {
            "id": ficha.id,
            "nome": ficha.apresentacao.nome_ficticio,
            "nivel": ficha.nivel_dificuldade,
        },
        "timer_minutes": req.timer_minutes,
    }
```

Atualizar `send_message`, `get_session`, `toggle_timer`, `start_timer`, `supervise`, `supervise_preview`, `get_rubric`, `end_session` — adicionar `user_id: str = Depends(get_current_user)` como parâmetro em cada um.

Para `end_session`, passar user_id para save_session:

```python
@app.delete("/api/sessions/{session_id}")
def end_session(
    session_id: str,
    user_id: str = Depends(get_current_user),
) -> dict:
    state = _sessions.pop(session_id, None)
    if not state:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    turns = len(state.agent.history) // 2
    duration = int(state.timer.elapsed_seconds) if state.timer else 0
    save_session(state.ficha.id, state.agent.history, duration_seconds=duration, user_id=user_id)
    return {"turns": turns}
```

Para `dashboard`, filtrar por user_id:

```python
@app.get("/api/dashboard")
def dashboard(user_id: str = Depends(get_current_user)) -> dict:
    return get_dashboard(user_id=user_id)
```

Adicionar endpoint de trajetória:

```python
@app.get("/api/users/me/trajectory")
def trajectory(user_id: str = Depends(get_current_user)) -> dict:
    from src.database import get_trajectory
    return {"sessions": get_trajectory(user_id)}
```

- [ ] **Step 3: Verificar que o servidor sobe**

```bash
cd /c/Users/vigna/.claude/psysim
uv run uvicorn src.api:app --reload --port 8000
```

Esperado: servidor sobe sem ImportError. Ctrl+C para parar.

- [ ] **Step 4: Commit**

```bash
git add src/api.py src/database.py
git commit -m "feat: protect all API endpoints with Supabase JWT auth"
```

---

### Task 4: Frontend — clientes Supabase e variáveis de ambiente

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/lib/supabase.ts`
- Create: `frontend/lib/supabase-server.ts`

- [ ] **Step 1: Instalar @supabase/ssr**

```bash
cd /c/Users/vigna/.claude/psysim/frontend
npm install @supabase/ssr @supabase/supabase-js
```

- [ ] **Step 2: Criar frontend/lib/supabase.ts (browser client)**

```typescript
import { createBrowserClient } from "@supabase/ssr";

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}
```

- [ ] **Step 3: Criar frontend/lib/supabase-server.ts (server client)**

```typescript
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

export async function createClient() {
  const cookieStore = await cookies();
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            );
          } catch {
            // middleware handles refresh
          }
        },
      },
    }
  );
}
```

- [ ] **Step 4: Adicionar variáveis ao .env local**

No arquivo `frontend/.env.local` (criar se não existir):

```
NEXT_PUBLIC_SUPABASE_URL=https://hepekrvzmpzzludivhjc.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon key do dashboard Supabase>
```

Para obter a anon key: Supabase Dashboard → Project Settings → API → `anon public`.

- [ ] **Step 5: Commit**

```bash
cd /c/Users/vigna/.claude/psysim
git add frontend/package.json frontend/package-lock.json frontend/lib/supabase.ts frontend/lib/supabase-server.ts
git commit -m "feat: add @supabase/ssr browser and server clients"
```

---

### Task 5: Middleware Next.js — proteção de rotas

**Files:**
- Create: `frontend/middleware.ts`

- [ ] **Step 1: Criar middleware.ts**

```typescript
import { createServerClient } from "@supabase/ssr";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
  let response = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value)
          );
          response = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options)
          );
        },
      },
    }
  );

  const {
    data: { user },
  } = await supabase.auth.getUser();

  const { pathname } = request.nextUrl;
  const isAuthPage = pathname === "/login" || pathname === "/register";

  if (!user && !isAuthPage) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (user && isAuthPage) {
    return NextResponse.redirect(new URL("/", request.url));
  }

  return response;
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
```

- [ ] **Step 2: Verificar que o dev server ainda sobe**

```bash
cd /c/Users/vigna/.claude/psysim/frontend
npm run dev
```

Esperado: servidor sobe em http://localhost:3000 e redireciona para /login (já que não há sessão). Ctrl+C.

- [ ] **Step 3: Commit**

```bash
cd /c/Users/vigna/.claude/psysim
git add frontend/middleware.ts
git commit -m "feat: add Next.js route protection middleware"
```

---

### Task 6: Páginas de login e cadastro

**Files:**
- Create: `frontend/components/AuthForm.tsx`
- Create: `frontend/app/login/page.tsx`
- Create: `frontend/app/register/page.tsx`

- [ ] **Step 1: Criar AuthForm.tsx**

```typescript
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase";

export default function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const supabase = createClient();

    try {
      if (mode === "login") {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
      } else {
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: { data: { name } },
        });
        if (error) throw error;
      }
      router.push("/");
      router.refresh();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro desconhecido";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center px-4"
      style={{ background: "var(--bg)" }}
    >
      <div
        className="w-full max-w-sm rounded-xl p-8"
        style={{ background: "var(--surface)", border: "1px solid var(--border)" }}
      >
        {/* Logo */}
        <div className="mb-8 text-center">
          <span className="font-bold text-xl tracking-tight" style={{ color: "var(--text)" }}>
            psysim
          </span>
          <p className="text-xs font-mono mt-1" style={{ color: "var(--text-faint)" }}>
            {mode === "login" ? "Entrar na conta" : "Criar conta"}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {mode === "register" && (
            <div className="flex flex-col gap-1.5">
              <label className="label">Nome</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Seu nome"
                required
                className="rounded-lg px-3 py-2.5 text-sm outline-none"
                style={{
                  background: "var(--bg)",
                  border: "1px solid var(--border)",
                  color: "var(--text)",
                }}
              />
            </div>
          )}

          <div className="flex flex-col gap-1.5">
            <label className="label">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="seu@email.com"
              required
              className="rounded-lg px-3 py-2.5 text-sm outline-none"
              style={{
                background: "var(--bg)",
                border: "1px solid var(--border)",
                color: "var(--text)",
              }}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="label">Senha</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Mínimo 6 caracteres"
              required
              minLength={6}
              className="rounded-lg px-3 py-2.5 text-sm outline-none"
              style={{
                background: "var(--bg)",
                border: "1px solid var(--border)",
                color: "var(--text)",
              }}
            />
          </div>

          {error && (
            <p
              className="text-xs rounded-lg px-3 py-2"
              style={{ background: "var(--red-bg)", color: "var(--red-fg)" }}
            >
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="mt-2 py-2.5 rounded-lg text-sm font-medium transition-opacity disabled:opacity-40"
            style={{ background: "var(--nav-bg)", color: "var(--nav-text)" }}
          >
            {loading ? "Aguarde..." : mode === "login" ? "Entrar" : "Criar conta"}
          </button>
        </form>

        <p className="text-center text-xs mt-6" style={{ color: "var(--text-faint)" }}>
          {mode === "login" ? (
            <>Não tem conta?{" "}
              <a href="/register" style={{ color: "var(--text-muted)" }}>Cadastre-se</a>
            </>
          ) : (
            <>Já tem conta?{" "}
              <a href="/login" style={{ color: "var(--text-muted)" }}>Entrar</a>
            </>
          )}
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Criar frontend/app/login/page.tsx**

```typescript
import AuthForm from "@/components/AuthForm";

export default function LoginPage() {
  return <AuthForm mode="login" />;
}
```

- [ ] **Step 3: Criar frontend/app/register/page.tsx**

```typescript
import AuthForm from "@/components/AuthForm";

export default function RegisterPage() {
  return <AuthForm mode="register" />;
}
```

- [ ] **Step 4: Testar manualmente**

```bash
cd /c/Users/vigna/.claude/psysim/frontend
npm run dev
```

Abrir http://localhost:3000 — deve redirecionar para /login. Criar conta em /register. Verificar que redireciona para / após login.

- [ ] **Step 5: Commit**

```bash
cd /c/Users/vigna/.claude/psysim
git add frontend/components/AuthForm.tsx frontend/app/login/page.tsx frontend/app/register/page.tsx
git commit -m "feat: add login and register pages with Supabase Auth"
```

---

### Task 7: Token de auth nos requests da API + AuthProvider + logout

**Files:**
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/app/layout.tsx`
- Modify: `frontend/app/page.tsx`

- [ ] **Step 1: Adicionar setAccessToken e authHeaders em api.ts**

Logo após a linha `const BASE = ...` no início de `frontend/lib/api.ts`, adicionar:

```typescript
let _accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  _accessToken = token;
}

function authHeaders(): Record<string, string> {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (_accessToken) h["Authorization"] = `Bearer ${_accessToken}`;
  return h;
}
```

- [ ] **Step 2: Atualizar todos os fetch em api.ts para usar authHeaders()**

Substituir cada `headers: { "Content-Type": "application/json" }` por `headers: authHeaders()`.

Substituir chamadas `fetch(url)` sem headers por `fetch(url, { headers: authHeaders() })`.

Lista de funções a atualizar:
- `listFichas` → `fetch(..., { headers: authHeaders() })`
- `startSession` → headers: authHeaders()
- `getSession` → headers: authHeaders()
- `endSession` → headers: authHeaders()
- `deleteSession` → headers: authHeaders()
- `toggleTimer` → headers: authHeaders()
- `getRubric` → headers: authHeaders()
- `getDashboard` → headers: authHeaders()
- `sendMessage` → headers: authHeaders()
- `startTimer` → headers: authHeaders()
- `saveSession` → headers: authHeaders()
- `makeStreamer` → adicionar parâmetro `extraHeaders: Record<string, string> = {}` e incluir no fetch

Para `makeStreamer`, substituir a assinatura por:

```typescript
function makeStreamer(
  url: string,
  body: object,
  onToken: (t: string) => void,
  onDone: () => void
): () => void {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      // ... resto igual
```

- [ ] **Step 3: Criar AuthProvider em frontend/app/layout.tsx**

Adicionar componente `AuthProvider` como client component. Criar `frontend/components/AuthProvider.tsx`:

```typescript
"use client";

import { useEffect } from "react";
import { createClient } from "@/lib/supabase";
import { setAccessToken } from "@/lib/api";

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const supabase = createClient();

    supabase.auth.getSession().then(({ data: { session } }) => {
      setAccessToken(session?.access_token ?? null);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setAccessToken(session?.access_token ?? null);
    });

    return () => subscription.unsubscribe();
  }, []);

  return <>{children}</>;
}
```

Em `frontend/app/layout.tsx`, importar e envolver `{children}` com `<AuthProvider>`:

```typescript
import AuthProvider from "@/components/AuthProvider";

// dentro do <body>:
<AuthProvider>
  {children}
</AuthProvider>
```

- [ ] **Step 4: Adicionar botão de logout ao nav em page.tsx**

Em `frontend/app/page.tsx`, adicionar botão Logout no `<nav>`. Criar `frontend/components/LogoutButton.tsx`:

```typescript
"use client";

import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase";
import { setAccessToken } from "@/lib/api";

export default function LogoutButton() {
  const router = useRouter();

  async function handleLogout() {
    const supabase = createClient();
    await supabase.auth.signOut();
    setAccessToken(null);
    router.push("/login");
    router.refresh();
  }

  return (
    <button
      onClick={handleLogout}
      className="text-xs font-mono px-2.5 h-7 rounded transition-colors hover:bg-white/10"
      style={{ color: "rgba(250,250,247,0.5)" }}
    >
      sair
    </button>
  );
}
```

Em `frontend/app/page.tsx`, no `<nav>`, adicionar após a data:

```typescript
import LogoutButton from "@/components/LogoutButton";

// No nav, após o span da data:
<LogoutButton />
```

- [ ] **Step 5: Commit**

```bash
cd /c/Users/vigna/.claude/psysim
git add frontend/lib/api.ts frontend/app/layout.tsx frontend/components/AuthProvider.tsx frontend/components/LogoutButton.tsx frontend/app/page.tsx
git commit -m "feat: wire auth token to all API calls + AuthProvider + logout"
```

---

### Task 8: Variáveis de ambiente no Railway e Vercel + SUPABASE_JWT_SECRET

- [ ] **Step 1: Adicionar SUPABASE_JWT_SECRET no Railway**

Obter o JWT secret: Supabase Dashboard → Project Settings → API → JWT Settings → `JWT Secret`.

No Railway: Variables → Add Variable:
```
SUPABASE_JWT_SECRET=<valor do JWT secret>
```

- [ ] **Step 2: Adicionar variáveis Supabase no Vercel**

```bash
cd /c/Users/vigna/.claude/psysim
vercel env add NEXT_PUBLIC_SUPABASE_URL production
# colar: https://hepekrvzmpzzludivhjc.supabase.co

vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
# colar: <anon key>
```

Após adicionar, redeploy obrigatório:
```bash
vercel --prod --yes --scope vignal
```

- [ ] **Step 3: Commit de .env.example atualizado**

Em `.env.example` (na raiz do projeto), adicionar:
```
SUPABASE_JWT_SECRET=your-jwt-secret-here
```

```bash
git add .env.example
git commit -m "chore: add SUPABASE_JWT_SECRET to .env.example"
```

---

## FASE 2 — Supervisor Preview: Ajuste para 5 turnos

---

### Task 9: Corrigir "last3" para 5 turnos + auth header no fetch inline

**Files:**
- Modify: `frontend/components/SessionView.tsx`

- [ ] **Step 1: Ajustar getHistorySlice**

Em `SessionView.tsx`, localizar a função `getHistorySlice` (linha ~89) e substituir:

```typescript
function getHistorySlice(mode: "realtime" | "session" | "last5") {
  if (mode === "session") return null;
  if (mode === "last5") return Math.max(0, messages.length - 10); // 5 exchanges = 10 messages
  return Math.max(0, messages.length - 2); // realtime = último 1 exchange = 2 messages
}
```

- [ ] **Step 2: Renomear "last3" para "last5" em todos os lugares de SessionView.tsx**

Substituir todas as ocorrências de `"last3"` por `"last5"` e `last3` por `last5`.

Substituir o label `⏪recente` por `⏪últimos 5t` na barra de supervisão (linha ~225).

Substituir o tipo de estado:
```typescript
const [supervisionMode, setSupervisionMode] = useState<"realtime" | "session" | "last5" | null>(null);
```

- [ ] **Step 3: Adicionar auth header no fetch inline de handleSupervise**

Na função `handleSupervise` (linha ~108), substituir:
```typescript
const res = await fetch(`${...}/api/sessions/${sessionId}/supervise-preview`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ approach, mode, history: historyToSend }),
});
```

por:
```typescript
import { authHeaders } from "@/lib/api"; // adicionar ao topo do arquivo
// ...
const res = await fetch(`${...}/api/sessions/${sessionId}/supervise-preview`, {
  method: "POST",
  headers: authHeaders(),
  body: JSON.stringify({ approach, mode, history: historyToSend }),
});
```

**Nota:** `authHeaders` precisa ser exportada de `api.ts`. Adicionar `export` na função `authHeaders` em `frontend/lib/api.ts`.

- [ ] **Step 4: Commit**

```bash
cd /c/Users/vigna/.claude/psysim
git add frontend/components/SessionView.tsx frontend/lib/api.ts
git commit -m "fix: supervisor preview uses 5 turns (was 3) + auth headers"
```

---

## FASE 3 — Rubrica Avançada

---

### Task 10: rubrica_data.py — dimensões por abordagem com âncoras

**Files:**
- Create: `src/rubrica_data.py`

- [ ] **Step 1: Criar src/rubrica_data.py**

```python
"""Dimensões de rubrica clínica por abordagem, com âncoras comportamentais por score."""

from typing import TypedDict


class Anchor(TypedDict):
    nome: str
    anchors: dict[int, str]  # score 1-5 -> descrição comportamental


RUBRICA_POR_ABORDAGEM: dict[str, list[Anchor]] = {
    "TCC": [
        {
            "nome": "Identificação de pensamentos automáticos",
            "anchors": {
                1: "Não tentou identificar pensamentos automáticos",
                2: "Mencionou pensamentos mas não os explorou",
                3: "Identificou alguns PAs com suporte do paciente",
                4: "Eliciou PAs específicos usando questionamento socrático",
                5: "Sistematicamente mapeou PAs com evidências e crenças centrais",
            },
        },
        {
            "nome": "Questionamento socrático",
            "anchors": {
                1: "Usou afirmações ou conselhos diretos em vez de perguntas",
                2: "Fez perguntas fechadas sem exploração guiada",
                3: "Usou algumas perguntas abertas de forma socrática básica",
                4: "Conduziu questionamento socrático para examinar evidências",
                5: "Usou diálogo socrático consistentemente para reestruturação cognitiva",
            },
        },
        {
            "nome": "Psicoeducação",
            "anchors": {
                1: "Não ofereceu nenhuma psicoeducação",
                2: "Psicoeducação genérica desconectada do caso",
                3: "Ofereceu psicoeducação básica ligada à queixa",
                4: "Psicoeducação clara, personalizada e bem integrada à sessão",
                5: "Psicoeducação precisa, oportunamente inserida, verificada com o paciente",
            },
        },
        {
            "nome": "Ativação comportamental",
            "anchors": {
                1: "Não abordou comportamento ou evitação",
                2: "Mencionou comportamento sem exploração ou planejamento",
                3: "Identificou padrões de evitação e discutiu alternativas básicas",
                4: "Explorou comportamento e esboçou ativação concreta",
                5: "Planejou ativação comportamental específica, graduada e colaborativa",
            },
        },
        {
            "nome": "Estruturação da sessão",
            "anchors": {
                1: "Sessão sem estrutura, objetivos ou agenda",
                2: "Esboço de agenda mas sem manutenção do foco",
                3: "Manteve alguma estrutura com desvios moderados",
                4: "Sessão bem estruturada com agenda e revisão ao final",
                5: "Estrutura TCC completa: agenda, revisão de tarefa, foco, tarefa, feedback",
            },
        },
    ],
    "Psicodinâmica": [
        {
            "nome": "Aliança terapêutica",
            "anchors": {
                1: "Postura distante ou crítica que comprometeu a aliança",
                2: "Aliança frágil, terapeuta pouco responsivo afetivamente",
                3: "Aliança básica estabelecida, empatia presente mas discreta",
                4: "Aliança sólida, terapeuta atento e responsivo emocionalmente",
                5: "Aliança profunda, reparação ativa de momentos de ruptura",
            },
        },
        {
            "nome": "Exploração histórica",
            "anchors": {
                1: "Não explorou história pessoal nem vínculos passados",
                2: "História mencionada de passagem sem aprofundamento",
                3: "Conectou queixa atual a alguns elementos históricos",
                4: "Explorou padrões históricos com ligações ao presente",
                5: "Articulou linha histórica coerente com impacto relacional claro",
            },
        },
        {
            "nome": "Interpretação e insights",
            "anchors": {
                1: "Não fez interpretações; ficou apenas no relato manifesto",
                2: "Interpretações prematuras ou sem base na transcrição",
                3: "Uma interpretação tentativa, bem fundamentada e oportuna",
                4: "Duas ou mais interpretações precisas com boa recepção do paciente",
                5: "Interpretações aprofundadas em camadas, gerou insight real",
            },
        },
        {
            "nome": "Trabalho com resistência",
            "anchors": {
                1: "Ignorou ou reforçou resistências",
                2: "Notou resistência mas não trabalhou com ela",
                3: "Nomeou resistência com alguma exploração",
                4: "Explorou resistência sem pressionar, mantendo aliança",
                5: "Trabalhou resistência habilmente, revelando função defensiva",
            },
        },
        {
            "nome": "Uso da transferência",
            "anchors": {
                1: "Não reconheceu dinâmicas transferenciais",
                2: "Dinâmica transferencial ignorada ou malmanejada",
                3: "Reconheceu transferência sem intervir diretamente",
                4: "Explorou dinâmica transferencial de forma contenida",
                5: "Usou transferência como material clínico central com precisão",
            },
        },
    ],
    "Humanista": [
        {
            "nome": "Empatia e presença",
            "anchors": {
                1: "Postura distante, respostas mecânicas ou avaliativas",
                2: "Empatia superficial ou inconsistente",
                3: "Presença empática básica, reflexos simples",
                4: "Empatia profunda, sintonizada ao mundo do paciente",
                5: "Presença plena, co-participação no mundo experiencial do paciente",
            },
        },
        {
            "nome": "Aceitação incondicional",
            "anchors": {
                1: "Julgamentos explícitos ou implícitos ao paciente",
                2: "Aceitação condicional ou seletiva perceptível",
                3: "Aceitação presente mas não comunicada com clareza",
                4: "Aceitação genuína comunicada verbal e não-verbalmente",
                5: "Aceitação incondicional clara e coerente ao longo de toda a sessão",
            },
        },
        {
            "nome": "Congruência e autenticidade",
            "anchors": {
                1: "Postura artificial, contradições entre fala e atitude",
                2: "Momentos de incongruência perceptíveis",
                3: "Razoavelmente autêntico com pequenas incongruências",
                4: "Congruente e genuíno na maior parte da sessão",
                5: "Total congruência, usou autorrevelação de forma terapêutica",
            },
        },
        {
            "nome": "Reflexo de sentimentos",
            "anchors": {
                1: "Não refletiu sentimentos, ficou nos fatos",
                2: "Reflexos imprecisos ou superficiais",
                3: "Alguns reflexos adequados de sentimentos explícitos",
                4: "Reflexos precisos de sentimentos explícitos e implícitos",
                5: "Reflexos profundos, capturou nuances emocionais e validou",
            },
        },
        {
            "nome": "Escuta ativa",
            "anchors": {
                1: "Interrompeu, desviou tópicos ou sobrepôs agenda própria",
                2: "Escuta passiva, respostas pouco ligadas ao que foi dito",
                3: "Escuta ativa básica, paráfrases simples",
                4: "Escuta ativa consistente com parafraseamento e sumarização",
                5: "Escuta profunda e responsiva, capturou implícitos e silêncios",
            },
        },
    ],
    "ACT": [
        {
            "nome": "Desfusão cognitiva",
            "anchors": {
                1: "Não trabalhou a relação do paciente com pensamentos",
                2: "Mencionou pensamentos sem promover distanciamento",
                3: "Uma tentativa básica de desfusão (nomeou o pensamento)",
                4: "Usou metáfora ou exercício de desfusão com clareza",
                5: "Paciente experienciou pensamento como evento mental (desfusão efetiva)",
            },
        },
        {
            "nome": "Aceitação e mindfulness",
            "anchors": {
                1: "Incentivou controle ou supressão de experiências internas",
                2: "Aceitação mencionada sem prática ou aprofundamento",
                3: "Convidou o paciente a observar experiências sem julgamento",
                4: "Promoveu aceitação ativa com exercício ou metáfora",
                5: "Trabalhou aceitação de forma experiencial, presente e consistente",
            },
        },
        {
            "nome": "Exploração de valores",
            "anchors": {
                1: "Não tocou em valores ou direções de vida",
                2: "Valores mencionados de forma superficial e genérica",
                3: "Explorou um valor com algum vínculo à queixa",
                4: "Clarificou valores importantes ligados ao sofrimento atual",
                5: "Mapeou valores centrais e os conectou a ações concretas",
            },
        },
        {
            "nome": "Ação comprometida",
            "anchors": {
                1: "Nenhuma orientação para ação baseada em valores",
                2: "Ação sugerida mas desconectada de valores",
                3: "Esboçou uma ação pequena ligada a um valor",
                4: "Definiu ações concretas alinhadas a valores clarificados",
                5: "Ações específicas, graduadas e comprometidas com valores do paciente",
            },
        },
        {
            "nome": "Flexibilidade psicológica",
            "anchors": {
                1: "Reforçou rigidez ou evitação experiencial",
                2: "Abordou evitação mas sem promover alternativa",
                3: "Promoveu alguma abertura a experiências difíceis",
                4: "Trabalhou hexaflex de forma integrada em momentos da sessão",
                5: "Sessão orientada consistentemente para flexibilidade psicológica",
            },
        },
    ],
    "Sistêmica": [
        {
            "nome": "Mapeamento de relações",
            "anchors": {
                1: "Não explorou contexto relacional ou familiar",
                2: "Mencionou relações sem mapeá-las",
                3: "Esboçou padrões relacionais básicos",
                4: "Mapeou relações com clareza, incluindo ciclos e papéis",
                5: "Construiu mapa relacional rico com padrões e recursos identificados",
            },
        },
        {
            "nome": "Pensamento circular",
            "anchors": {
                1: "Pensamento linear sobre causas e culpas",
                2: "Alguma circularidade mas ainda predominantemente causal",
                3: "Usou perguntas circulares básicas",
                4: "Explorou circularidade com consistência, conectou padrões",
                5: "Pensamento sistêmico claro: padrões, feedbacks e recursividade",
            },
        },
        {
            "nome": "Neutralidade sistêmica",
            "anchors": {
                1: "Tomou partido ou validou versão de um membro da família",
                2: "Neutralidade comprometida em momentos da sessão",
                3: "Manteve neutralidade básica sem explorar múltiplas perspectivas",
                4: "Neutralidade ativa, convidou múltiplos pontos de vista",
                5: "Curiosidade sistêmica genuína, neutralidade mantida consistentemente",
            },
        },
        {
            "nome": "Metáforas e recursos",
            "anchors": {
                1: "Nenhuma metáfora ou recurso do sistema utilizado",
                2: "Metáfora introduzida mas não desenvolvida",
                3: "Usou metáfora ou recurso do paciente de forma básica",
                4: "Explorou metáforas e recursos do sistema com eficácia",
                5: "Metáforas sistêmicas centrais, ampliou recursos do sistema habilmente",
            },
        },
        {
            "nome": "Tarefas sistêmicas",
            "anchors": {
                1: "Nenhuma tarefa ou diretiva prescrita",
                2: "Tarefa genérica sem ligação ao sistema",
                3: "Tarefa simples, coerente com o padrão identificado",
                4: "Tarefa sistêmica específica, colaborativa e com fundamento claro",
                5: "Tarefa criativa, paradoxal ou ritual alinhada ao sistema e aos objetivos",
            },
        },
    ],
    "Integrativa": [
        {
            "nome": "Flexibilidade técnica",
            "anchors": {
                1: "Aplicou técnicas de uma só abordagem rigidamente",
                2: "Tentou integrar mas de forma incoerente ou mecânica",
                3: "Transitou entre técnicas de forma básica",
                4: "Integrou técnicas de forma fluida e contextualizada",
                5: "Integração sofisticada, técnicas escolhidas conforme necessidade do momento",
            },
        },
        {
            "nome": "Formulação integrativa",
            "anchors": {
                1: "Nenhuma formulação; respondeu reativamente",
                2: "Formulação fragmentada, sem coerência entre lentes",
                3: "Formulação básica usando elementos de mais de uma abordagem",
                4: "Formulação integrativa clara ligando diferentes perspectivas",
                5: "Formulação rica e coerente, articulou múltiplas lentes elegantemente",
            },
        },
        {
            "nome": "Uso de múltiplas lentes",
            "anchors": {
                1: "Apenas uma perspectiva teórica utilizada",
                2: "Duas perspectivas justapostas mas não integradas",
                3: "Usou múltiplas lentes de forma básica e compatível",
                4: "Integrou perspectivas de forma complementar e oportuna",
                5: "Múltiplas lentes usadas fluidamente, enriquecendo a compreensão do caso",
            },
        },
        {
            "nome": "Coerência interna",
            "anchors": {
                1: "Intervenções contraditórias entre si",
                2: "Algumas incoerências entre objetivos e intervenções",
                3: "Coerência razoável com pequenos desvios",
                4: "Intervenções coerentes com a formulação e objetivo da sessão",
                5: "Coerência total: cada intervenção serve a um propósito integrado claro",
            },
        },
        {
            "nome": "Adaptação ao paciente",
            "anchors": {
                1: "Abordagem padronizada ignorando características do paciente",
                2: "Alguma adaptação mas predominantemente técnica-centrada",
                3: "Ajustes básicos ao estilo e necessidade do paciente",
                4: "Adaptação clara ao paciente, técnicas ajustadas ao caso",
                5: "Altamente personalizado, abordagem moldada pelo paciente em tempo real",
            },
        },
    ],
}


def get_dimensoes(approach: str) -> list[Anchor]:
    """Retorna dimensões da abordagem, com fallback para lista genérica."""
    return RUBRICA_POR_ABORDAGEM.get(approach, RUBRICA_POR_ABORDAGEM["TCC"])


def get_nomes(approach: str) -> list[str]:
    return [d["nome"] for d in get_dimensoes(approach)]


def get_anchor_text(approach: str, nome: str, score: int) -> str:
    for d in get_dimensoes(approach):
        if d["nome"] == nome:
            return d["anchors"].get(score, "")
    return ""
```

- [ ] **Step 2: Smoke test**

```bash
cd /c/Users/vigna/.claude/psysim
python -c "
from src.rubrica_data import get_dimensoes, get_anchor_text
dims = get_dimensoes('TCC')
print(len(dims), 'dimensoes')
print(get_anchor_text('TCC', 'Questionamento socrático', 3))
"
```

Esperado:
```
5 dimensoes
Usou algumas perguntas abertas de forma socrática básica
```

- [ ] **Step 3: Commit**

```bash
git add src/rubrica_data.py
git commit -m "feat: add rubrica_data.py with per-approach dimensions and behavioral anchors"
```

---

### Task 11: Atualizar supervisor_agent.py para usar rubrica_data

**Files:**
- Modify: `src/supervisor_agent.py`

- [ ] **Step 1: Substituir RUBRICA_DIMENSOES por rubrica_data**

No `supervisor_agent.py`, remover a constante `RUBRICA_DIMENSOES` (linhas 23–30) e adicionar import:

```python
from src.rubrica_data import get_dimensoes, get_nomes, get_anchor_text
```

Remover também a definição `RUBRICA_DIMENSOES = [...]`.

- [ ] **Step 2: Atualizar _build_rubrica_prompt para incluir âncoras**

Substituir a função `_build_rubrica_prompt` por:

```python
def _build_rubrica_prompt(ficha: Ficha, approach_key: str) -> str:
    a = ficha.apresentacao
    approach_desc = APPROACHES.get(approach_key, approach_key)
    dimensoes = get_dimensoes(approach_key)

    dims_text = ""
    for d in dimensoes:
        dims_text += f"\n**{d['nome']}**\n"
        for score in range(1, 6):
            dims_text += f"  {score}: {d['anchors'][score]}\n"

    enrich = ""
    if ficha.consciencia and ficha.consciencia.nao_tem_consciencia_de:
        enrich += (
            f"\nPadrões que o paciente não tem consciência (observe se o trainee identificou):\n- "
            + "\n- ".join(ficha.consciencia.nao_tem_consciencia_de)
        )

    nomes_json = "\n".join(f'    {{"nome": "{d["nome"]}", "score": N, "justificativa": "..."}},' for d in dimensoes)

    return f"""Você é um supervisor clínico avaliando uma sessão de treino.

Contexto do caso:
- Paciente: {a.nome_ficticio}, {a.idade} anos, {a.genero}, {a.ocupacao}
- Queixa: {ficha.queixa_principal}
- Abordagem avaliada: {approach_key} — {approach_desc}
{enrich}

Avalie a sessão nas dimensões abaixo. Para cada dimensão, escolha o score (1–5) cuja descrição melhor descreve o que apareceu na transcrição. Baseie-se EXCLUSIVAMENTE no que está na transcrição.

{dims_text}

Retorne APENAS JSON válido, sem texto fora do JSON:
{{
  "dimensoes": [
{nomes_json}
  ]
}}"""
```

- [ ] **Step 3: Atualizar get_rubrica para incluir anchor no retorno**

Atualizar o dataclass `DimensaoRubrica`:

```python
@dataclass
class DimensaoRubrica:
    nome: str
    score: int       # 1–5
    justificativa: str
    anchor: str = "" # texto da âncora para o score dado
```

Atualizar `get_rubrica` para preencher o campo `anchor`:

```python
def get_rubrica(
    self, ficha: Ficha, history: list[dict[str, str]], approach: str
) -> list[DimensaoRubrica]:
    transcript = _format_transcript(ficha.apresentacao.nome_ficticio, history)
    resp = self.client.chat.completions.create(
        model=self.model,
        messages=[
            {"role": "system", "content": _build_rubrica_prompt(ficha, approach)},
            {"role": "user", "content": f"Transcrição:\n\n{transcript}"},
        ],
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content or "{}"
    data = json.loads(raw)
    return [
        DimensaoRubrica(
            nome=d["nome"],
            score=max(1, min(5, int(d["score"]))),
            justificativa=d.get("justificativa", ""),
            anchor=get_anchor_text(approach, d["nome"], max(1, min(5, int(d["score"])))),
        )
        for d in data.get("dimensoes", [])
    ]
```

- [ ] **Step 4: Atualizar o endpoint /rubric em api.py para retornar anchor**

Em `api.py`, no endpoint `get_rubric`, atualizar a serialização:

```python
return {
    "approach": approach,
    "dimensoes": [
        {
            "nome": d.nome,
            "score": d.score,
            "justificativa": d.justificativa,
            "anchor": d.anchor,
        }
        for d in dimensoes
    ],
}
```

- [ ] **Step 5: Verificar que servidor sobe sem erro**

```bash
uv run uvicorn src.api:app --reload --port 8000
```

Esperado: sem ImportError.

- [ ] **Step 6: Commit**

```bash
git add src/supervisor_agent.py src/api.py
git commit -m "feat: supervisor uses per-approach rubric dimensions with behavioral anchors"
```

---

### Task 12: Atualizar RubricaView — âncoras + dimensões por abordagem

**Files:**
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/components/RubricaView.tsx`

- [ ] **Step 1: Atualizar DimensaoRubrica em api.ts**

Em `frontend/lib/api.ts`, no interface `DimensaoRubrica`:

```typescript
export interface DimensaoRubrica {
  nome: string;
  score: number;
  justificativa: string;
  anchor: string;
}
```

- [ ] **Step 2: Atualizar RubricaView para mostrar âncora**

Substituir `RubricaView.tsx` inteiro por:

```typescript
"use client";

import { useState } from "react";
import type { DimensaoRubrica } from "@/lib/api";

function scoreColor(score: number): { bg: string; fg: string } {
  if (score <= 2) return { bg: "var(--red-bg)",    fg: "var(--red-fg)" };
  if (score === 3) return { bg: "var(--yellow-bg)", fg: "var(--yellow-fg)" };
  return              { bg: "var(--green-bg)",   fg: "var(--green-fg)" };
}

function ScoreDots({ score, fg }: { score: number; fg: string }) {
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
  const [expanded, setExpanded] = useState<string | null>(null);
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
          const isOpen = expanded === d.nome;
          return (
            <div key={d.nome} className="px-5 py-4">
              <button
                className="w-full text-left"
                onClick={() => setExpanded(isOpen ? null : d.nome)}
              >
                <div className="flex items-start justify-between gap-4 mb-2">
                  <span className="text-sm font-medium" style={{ color: "var(--text)" }}>
                    {d.nome}
                  </span>
                  <div className="flex items-center gap-2 shrink-0">
                    <ScoreDots score={d.score} fg={fg} />
                    <span className="text-xs font-mono font-bold w-6 text-right" style={{ color: fg }}>
                      {d.score}/5
                    </span>
                  </div>
                </div>
              </button>

              {/* Justificativa */}
              {d.justificativa && (
                <p className="text-xs leading-relaxed mb-2" style={{ color: "var(--text-muted)" }}>
                  {d.justificativa}
                </p>
              )}

              {/* Âncora — expandível */}
              {isOpen && d.anchor && (
                <div
                  className="text-xs rounded-lg px-3 py-2 mt-1"
                  style={{ background: bg, color: fg, border: `1px solid ${fg}` }}
                >
                  <span className="font-mono font-bold mr-1">{d.score}:</span>
                  {d.anchor}
                </div>
              )}

              {/* Toggle anchor */}
              {d.anchor && (
                <button
                  onClick={() => setExpanded(isOpen ? null : d.nome)}
                  className="text-xs font-mono mt-1 transition-colors"
                  style={{ color: "var(--text-faint)" }}
                >
                  {isOpen ? "▲ ocultar âncora" : "▼ ver âncora comportamental"}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
cd /c/Users/vigna/.claude/psysim
git add frontend/lib/api.ts frontend/components/RubricaView.tsx
git commit -m "feat: RubricaView shows behavioral anchors per score (expandable)"
```

---

### Task 13: Endpoint de trajetória + componente TrajectoryChart

**Files:**
- Create: `frontend/components/TrajectoryChart.tsx`
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/components/DashboardStats.tsx`

- [ ] **Step 1: Adicionar getTrajectory em api.ts**

```typescript
export interface TrajectoryEntry {
  id: string;
  session_id: string;
  approach: string;
  rubric_scores: DimensaoRubrica[];
  created_at: string;
}

export async function getTrajectory(): Promise<TrajectoryEntry[]> {
  const res = await fetch(`${BASE}/api/users/me/trajectory`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Erro ao carregar trajetória");
  const data = await res.json();
  return data.sessions as TrajectoryEntry[];
}
```

- [ ] **Step 2: Criar frontend/components/TrajectoryChart.tsx**

```typescript
"use client";

import { useEffect, useState } from "react";
import { getTrajectory, type TrajectoryEntry } from "@/lib/api";

function scoreColor(score: number): string {
  if (score <= 2) return "var(--red-fg)";
  if (score === 3) return "var(--yellow-fg)";
  return "var(--green-fg)";
}

function scoreBg(score: number): string {
  if (score <= 2) return "var(--red-bg)";
  if (score === 3) return "var(--yellow-bg)";
  return "var(--green-bg)";
}

export default function TrajectoryChart() {
  const [entries, setEntries] = useState<TrajectoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    getTrajectory()
      .then(setEntries)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <p className="text-xs font-mono" style={{ color: "var(--text-faint)" }}>
        carregando trajetória...
      </p>
    );
  }

  if (error || entries.length === 0) return null;

  // Collect all unique dimension names across entries
  const allDims = Array.from(
    new Set(entries.flatMap((e) => e.rubric_scores.map((r) => r.nome)))
  );

  // Keep at most last 8 sessions for readability
  const recent = entries.slice(-8);

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
                style={{ color: "var(--text-faint)", minWidth: 200 }}>
                Dimensão
              </th>
              {recent.map((e, i) => (
                <th key={e.id} className="px-2 py-2 text-center font-mono font-normal"
                  style={{ color: "var(--text-faint)", minWidth: 56 }}>
                  S{entries.length - recent.length + i + 1}
                  <br />
                  <span style={{ fontSize: "0.65rem" }}>{e.approach.slice(0, 3)}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {allDims.map((dim) => (
              <tr key={dim} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                <td className="px-4 py-2 font-mono" style={{ color: "var(--text-muted)" }}>
                  {dim}
                </td>
                {recent.map((entry) => {
                  const score = entry.rubric_scores.find((r) => r.nome === dim)?.score;
                  return (
                    <td key={entry.id} className="px-2 py-2 text-center">
                      {score !== undefined ? (
                        <span
                          className="inline-block w-7 h-7 rounded text-xs font-mono font-bold leading-7"
                          style={{
                            background: scoreBg(score),
                            color: scoreColor(score),
                          }}
                        >
                          {score}
                        </span>
                      ) : (
                        <span style={{ color: "var(--text-faint)" }}>—</span>
                      )}
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
```

- [ ] **Step 3: Adicionar TrajectoryChart ao DashboardStats**

Em `frontend/components/DashboardStats.tsx`, importar e renderizar o componente após o bloco de stats existente.

Verificar o arquivo atual para encontrar onde termina o último bloco, e adicionar após ele:

```typescript
import TrajectoryChart from "@/components/TrajectoryChart";

// No JSX, adicionar após o último elemento atual:
<TrajectoryChart />
```

**Nota:** `DashboardStats` é provavelmente um server component. `TrajectoryChart` é client (tem useEffect). Isso é compatível — client components podem ser filhos de server components.

- [ ] **Step 4: Commit**

```bash
cd /c/Users/vigna/.claude/psysim
git add frontend/lib/api.ts frontend/components/TrajectoryChart.tsx frontend/components/DashboardStats.tsx
git commit -m "feat: trajectory chart on dashboard (score evolution across sessions)"
```

---

## FASE 4 — Deploy

---

### Task 14: Push e deploy

- [ ] **Step 1: Verificar que tudo compila localmente**

```bash
cd /c/Users/vigna/.claude/psysim/frontend
npm run build
```

Esperado: build sem erros TypeScript.

```bash
cd /c/Users/vigna/.claude/psysim
uv run uvicorn src.api:app --port 8000
```

Esperado: servidor sobe sem erros.

- [ ] **Step 2: Push para GitHub**

```bash
cd /c/Users/vigna/.claude/psysim
git push origin main
```

Railway e Vercel fazem redeploy automático ao detectar push.

- [ ] **Step 3: Verificar Railway**

Aguardar deploy no Railway (2–3 min). Verificar logs: sem erros de importação, `Application startup complete`.

- [ ] **Step 4: Verificar Vercel**

Aguardar deploy no Vercel. Abrir https://psysim-cc.vercel.app — deve redirecionar para /login.

- [ ] **Step 5: Smoke test em produção**

1. Criar conta em /register
2. Fazer login em /login — redireciona para /
3. Dashboard carrega (dashboard vazio é esperado para conta nova)
4. Iniciar sessão com um paciente — deve funcionar
5. Usar supervisor preview (3 botões) durante sessão
6. Encerrar sessão — supervisão + rubrica (com âncoras)
7. Dashboard mostra stats da sessão recém-concluída
8. Logout — redireciona para /login

---

## Checklist de auto-revisão

- [x] Auth protege todos os endpoints (fichas é público, tudo mais exige token)
- [x] user_id salvo em sessions, supervisions, active_sessions
- [x] dashboard filtrado por user_id
- [x] trajectory endpoint filtrado por user_id
- [x] supervisor preview usa 5 turnos (não 3)
- [x] rubrica_data.py tem 5 dimensões × 6 abordagens = 30 dimensões, cada uma com âncoras 1–5
- [x] âncora é retornada pela API e mostrada no RubricaView de forma expandível
- [x] TrajectoryChart mostra score por sessão × dimensão (tabela colorida, sem dependência nova)
- [x] tipos TypeScript consistentes entre api.ts, RubricaView.tsx, TrajectoryChart.tsx
- [x] SUPABASE_JWT_SECRET documentado no .env.example e necessário no Railway
- [x] `authHeaders()` exportado para uso em SessionView
