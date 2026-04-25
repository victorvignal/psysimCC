# psysim — Handoff completo para nova sessão

## O que é este projeto

Simulador de pacientes com IA para estudantes de psicologia praticarem entrevista clínica antes de atendimentos reais. O estudante conversa com um agente que encena um paciente, e depois recebe supervisão estruturada com feedback narrativo e rubrica de competências.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12, FastAPI, uvicorn |
| LLM | DeepSeek v4-flash via OpenRouter (API compatível com OpenAI SDK) |
| Supervisão | Mesmo modelo, prompt separado, JSON mode para rubrica |
| Frontend | Next.js 16 (App Router), TypeScript, Tailwind v4 |
| Banco de dados | Supabase (PostgreSQL) |
| Gerenciador Python | uv |
| Deploy backend | Railway (Docker) |
| Deploy frontend | Vercel |
| Repo | https://github.com/victorvignal/psysimCC |

---

## Estrutura de pastas

```
psysim/
├── src/                        # Backend Python
│   ├── api.py                  # FastAPI — todos os endpoints REST
│   ├── patient_agent.py        # Agente-paciente (LLM em personagem)
│   ├── supervisor_agent.py     # Supervisor pós-sessão (feedback + rubrica)
│   ├── ficha_loader.py         # Pydantic — carrega e valida YAML das fichas
│   ├── database.py             # Supabase — salva sessões, supervisões, dashboard
│   ├── timer.py                # SessionTimer com pausa/retomada
│   ├── session.py              # Interface terminal (rich) — mantida para debug local
│   ├── app.py                  # Interface Chainlit — legada, não usada em prod
│   ├── generator.py            # Gera fichas YAML a partir de texto livre
│   └── voice.py                # TTS via Minimax — legado, não usado em prod
├── frontend/                   # Next.js
│   ├── app/
│   │   ├── page.tsx            # Tela 1 — seleção de paciente + dashboard
│   │   ├── layout.tsx          # Layout global (fonts, metadata)
│   │   └── session/[sessionId]/
│   │       ├── page.tsx        # Tela 2 — chat com o paciente
│   │       └── supervision/
│   │           └── page.tsx    # Tela 3 — supervisão pós-sessão
│   ├── components/
│   │   ├── PatientGrid.tsx     # Cards de seleção de paciente
│   │   ├── SessionView.tsx     # Chat + sidebar (ficha, abordagem, notas)
│   │   ├── SupervisionView.tsx # Feedback narrativo + rubrica em paralelo
│   │   ├── RubricaView.tsx     # Escala visual 1–5 por competência
│   │   └── DashboardStats.tsx  # Stats + barras de progresso por competência
│   └── lib/
│       └── api.ts              # Cliente TypeScript tipado para todos os endpoints
├── fichas/
│   └── validated/
│       └── maria_01.yaml       # Ficha canônica — referência de schema
├── Dockerfile                  # Para Railway — roda uvicorn na porta 8000
├── pyproject.toml              # Dependências Python (uv)
└── .env                        # Variáveis locais (não commitado)
```

---

## Fichas de paciente (YAML)

Fichas ficam em `fichas/validated/`. O schema canônico é `maria_01.yaml`.

Campos principais:
- `apresentacao` — nome, idade, gênero, ocupação (visíveis ao terapeuta)
- `queixa_principal` — fala do paciente
- `sintomas_ativos`, `historia_pregressa`, `historia_familiar`, `gatilho_atual`
- `comportamento` — estilo de comunicação, defesas, resistências, red flags
- `_uso_interno` — diagnóstico, formulação psicodinâmica/TCC, temas evitados

**Importante:** `_uso_interno` NÃO entra no prompt do agente-paciente. Entra apenas no supervisor. Isso simula um paciente real que não entrega o diagnóstico pronto.

---

## Backend — `src/api.py`

FastAPI rodando em `http://localhost:8000` (dev) ou Railway (prod).

### Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/fichas` | Lista todas as fichas em `fichas/validated/` |
| POST | `/api/sessions` | Cria sessão `{ficha_id, timer_minutes}` → `{session_id}` |
| GET | `/api/sessions/{id}` | Estado da sessão (nome, nível, turnos, timer, abordagens) |
| POST | `/api/sessions/{id}/message` | Envia mensagem → `{content}` (resposta completa, JSON) |
| POST | `/api/sessions/{id}/supervise` | SSE — stream do feedback narrativo |
| POST | `/api/sessions/{id}/rubric` | JSON — rubrica 6 dimensões 1-5 |
| POST | `/api/sessions/{id}/timer/toggle` | Pausa/retoma timer |
| DELETE | `/api/sessions/{id}` | Encerra sessão + salva no Supabase |
| GET | `/api/dashboard` | Stats + progresso por competência |

### Sessões em memória vs Supabase

Sessões ativas ficam em `_sessions: dict[str, SessionState]` (memória). A cada turno, o histórico é persistido em `active_sessions` no Supabase via `_persist_session()`. Se o Railway reiniciar, `_load_session()` recupera do Supabase automaticamente.

### CORS

Controlado pela variável `ALLOWED_ORIGINS` (separada por vírgula). Default: `http://localhost:3000`.

### Bug conhecido e corrigido

O Railway adiciona `\n` no final de variáveis de ambiente. A `OPENROUTER_API_KEY` precisou de `.strip()` ao ser lida:
```python
api_key=(os.getenv("OPENROUTER_API_KEY") or "").strip()
```
Sem isso, o HTTP header ficava inválido e todas as chamadas ao OpenRouter falhavam silenciosamente.

---

## Agentes LLM

### PatientAgent (`patient_agent.py`)

- `build_patient_prompt(ficha)` — monta system prompt a partir da ficha YAML
- `respond(message)` — chamada síncrona (usada em produção via `asyncio.to_thread`)
- `respond_async(message)` — wrapper async que usa `asyncio.to_thread(self.respond, ...)`
- `respond_stream(message)` — gerador async com streaming (não usado em produção — Railway/Fastly CDN bufferiza SSE)

**Por que `asyncio.to_thread`?** O cliente async do OpenAI SDK tem problemas de conexão no ambiente Railway (`LocalProtocolError: Illegal header value`). O cliente síncrono funciona. `asyncio.to_thread` roda o síncrono em thread pool sem bloquear o event loop.

### SupervisorAgent (`supervisor_agent.py`)

- `supervise_stream(ficha, history, approach)` — feedback narrativo em 6 seções (SSE) — usado apenas localmente
- `get_rubrica(ficha, history, approach)` — rubrica estruturada em JSON mode

**Rubrica — 6 dimensões:**
1. Empatia e validação
2. Formulação de caso
3. Técnica de entrevista
4. Manejo de resistência
5. Aliança terapêutica
6. Planejamento terapêutico

Cada dimensão: nota 1–5 + justificativa curta baseada exclusivamente na transcrição.

**Importante:** o supervisor NÃO recebe diagnóstico nem formulação da ficha — só queixa principal e dados de apresentação. O resto vem apenas da transcrição. Isso evita spoiler de material clínico que o estudante deveria descobrir sozinho.

---

## Frontend — Next.js

### Design tokens (`globals.css`)

```css
--bg: #f5f0e8          /* fundo creme */
--surface: #fafaf7     /* cards/painéis */
--nav-bg: #1a1a1a      /* navbar */
--green-bg/fg          /* iniciante / positivo */
--blue-bg/fg           /* neutro / informação */
--yellow-bg/fg         /* atenção */
--red-bg/fg            /* avançado / erro */
--bubble-patient: #ede9e2    /* balão do paciente */
--bubble-therapist: #d4dce8  /* balão do terapeuta */
```

Font: Geist (body) + Space Mono (labels, metadados, timestamps).

### Fluxo de navegação

```
/ (Tela 1 — seleção)
  → /session/[sessionId] (Tela 2 — chat)
    → /session/[sessionId]/supervision (Tela 3 — supervisão)
      → / (nova sessão)
```

### Tela 1 — `page.tsx` + `PatientGrid` + `DashboardStats`

- Server Component: busca fichas e dashboard em paralelo no servidor
- `DashboardStats`: 4 métricas + barras de progresso por competência (médias dos rubric_scores salvos)
- `PatientGrid`: cards com header colorido por nível, queixa, botão iniciar

### Tela 2 — `SessionView`

- Sidebar direita (lg+): ficha, seletor de abordagem, notas pessoais
- Abordagem selecionada é passada para supervisão via query param
- Timer: botão toggle na topbar, barra de detalhe expansível
- Envio: `sendMessage()` → POST JSON → resposta completa (não streaming — CDN bloqueia SSE)
- Ao encerrar: navega para supervisão SEM deletar a sessão (sessão é deletada quando o usuário sair da página de supervisão via `useEffect` cleanup)

### Tela 3 — `SupervisionView` + `RubricaView`

- Layout 2 colunas (lg+): rubrica à esquerda, feedback narrativo à direita
- Rubrica e narrativa são disparadas em paralelo (`getRubric` + `streamSupervision`)
- `RubricaView`: 5 quadradinhos por dimensão, coloridos por score (verde ≥4, amarelo =3, vermelho ≤2), média geral no header
- Markdown rendering via `react-markdown`

### `lib/api.ts`

Todos os endpoints tipados. Função `makeStreamer()` para SSE (supervisão) com:
- `finally { onDone() }` — garante que o loading sempre termina
- `reader.cancel()` ao receber evento `done` — encerra o loop sem depender do proxy fechar a conexão

---

## Banco de dados — Supabase

Projeto: `hepekrvzmpzzludivhjc`

### Tabelas

**`sessions`** — histórico de sessões encerradas
```sql
id uuid PK, ficha_id text, turns jsonb,
metadata jsonb, created_at timestamptz, duration_seconds integer
```

**`supervisions`** — supervisões realizadas
```sql
id uuid PK, session_id uuid FK→sessions,
approach text, feedback text,
rubric_scores jsonb,  -- [{nome, score, justificativa}, ...]
created_at timestamptz
```

**`active_sessions`** — snapshot de sessões em andamento (para sobreviver restarts)
```sql
id uuid PK, ficha_id text, history jsonb,
timer_minutes integer, elapsed_seconds integer,
approach text, created_at timestamptz, updated_at timestamptz
```

---

## Variáveis de ambiente

### Backend (Railway)

```
OPENROUTER_API_KEY=sk-or-v1-...   # chave OpenRouter — ATENÇÃO: Railway adiciona \n, o código faz .strip()
MODEL_ID=deepseek/deepseek-v4-flash
SUPERVISOR_MODEL_ID=              # opcional — se vazio usa MODEL_ID
SUPABASE_URL=https://hepekrvzmpzzludivhjc.supabase.co
SUPABASE_KEY=sb_publishable_...
ALLOWED_ORIGINS=https://psysim-cc.vercel.app
SESSION_DURATION_MINUTES=0        # 0 = sem timer
```

### Frontend (Vercel)

```
NEXT_PUBLIC_API_URL=https://psysimcc-production.up.railway.app
```

**Atenção:** variáveis `NEXT_PUBLIC_` são embutidas no build — após alterar é obrigatório redeployar.

---

## Como rodar localmente

```bash
# Backend
cd psysim
uv sync
uv run uvicorn src.api:app --reload --port 8000

# Frontend (outro terminal)
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

---

## Deploy

- **Railway**: detecta `Dockerfile` automaticamente. Push para `main` no GitHub dispara redeploy.
- **Vercel**: Root Directory = `frontend`. Push para `main` dispara redeploy.
- **Deploy manual via CLI**: `vercel --prod --yes --scope vignal` (a partir da raiz do repo, não de `frontend/`)

---

## O que está pendente

| Item | Status |
|---|---|
| Supervisor em tempo real (por turno / últimas N trocas) | Não implementado |
| Botões de reação no supervisor (👍 útil / 🤔 discordo / 🚩 ignorar) | Não implementado |
| Dashboard 1C completo (sessões recentes, desbloqueio por nível) | Parcialmente implementado (stats + progresso) |
| TTS (voz do paciente) | Implementado no terminal, não na web |
| Gerador de fichas via web | Só via CLI (`uv run gerador`) |
| Autenticação de usuário | Não implementado |
| SSE funcional em produção | Bloqueado pelo Fastly CDN do Railway — workaround: JSON para mensagens |

---

## Problemas conhecidos e soluções aplicadas

| Problema | Causa | Solução |
|---|---|---|
| `APIConnectionError` em produção | Railway adiciona `\n` em env vars | `.strip()` na API key |
| SSE streaming trava indefinidamente | Fastly CDN bufferiza a resposta | Endpoint `/message` retorna JSON simples |
| Sessões perdidas no restart do Railway | Sessões só em memória | Persistência em `active_sessions` no Supabase |
| Supervisor dava "spoiler" do diagnóstico | Diagnóstico/formulação estavam no system prompt | Removidos — supervisor só vê queixa + transcrição |
| Tokens duplicados no streaming | Mutação de objeto dentro de updater React no Strict Mode | Criar novo objeto com spread em vez de mutar |
| Deploy Vercel sem `NEXT_PUBLIC_API_URL` | Var não configurada antes do primeiro build | Adicionada via CLI e redeployado |
