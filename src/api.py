import json
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from src.database import get_dashboard, save_session, save_supervision
from src.ficha_loader import Ficha, load_ficha
from src.patient_agent import PatientAgent
from src.supervisor_agent import APPROACHES, SupervisorAgent, RUBRICA_DIMENSOES
from src.timer import SessionTimer

app = FastAPI(title="Simulador Clínico API")

_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
_origins = [o.strip() for o in _raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

_FICHAS_DIR = Path(__file__).parent.parent / "fichas" / "validated"


# ── Session state ──────────────────────────────────────────────

@dataclass
class SessionState:
    ficha: Ficha
    agent: PatientAgent
    timer: SessionTimer | None = None
    approach: str = "TCC"
    last_supervision: str = ""


_sessions: dict[str, SessionState] = {}


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
            "updated_at": "now()",
        }).execute()
    except Exception:
        pass


def _load_session(session_id: str) -> SessionState | None:
    from src.database import _get_client
    client = _get_client()
    if not client:
        return None
    try:
        result = client.table("active_sessions").select("*").eq("id", session_id).execute()
        if not result.data:
            return None
        row = result.data[0]
        path = _FICHAS_DIR / f"{row['ficha_id']}.yaml"
        if not path.exists():
            return None
        ficha = load_ficha(path)
        agent = PatientAgent(ficha)
        agent.history = row.get("history") or []
        timer = SessionTimer(row["timer_minutes"]) if row.get("timer_minutes", 0) > 0 else None
        return SessionState(ficha=ficha, agent=agent, timer=timer, approach=row.get("approach", "TCC"))
    except Exception:
        return None


# ── Request / response models ──────────────────────────────────

class StartSessionRequest(BaseModel):
    ficha_id: str
    timer_minutes: int = 0


class MessageRequest(BaseModel):
    content: str


class SupervisePreviewRequest(BaseModel):
    approach: str = "TCC"
    mode: str = "session"
    history: list[dict[str, str]]


# ── Endpoints ─────────────────────────────────────────────────

@app.get("/api/fichas")
def list_fichas() -> list[dict]:
    fichas = []
    for path in sorted(_FICHAS_DIR.glob("*.yaml")):
        try:
            f = load_ficha(path)
            fichas.append({
                "id": f.id,
                "nome": f.apresentacao.nome_ficticio,
                "idade": f.apresentacao.idade,
                "genero": f.apresentacao.genero,
                "ocupacao": f.apresentacao.ocupacao,
                "queixa": f.queixa_principal,
                "nivel": f.nivel_dificuldade,
            })
        except Exception:
            continue
    return fichas


@app.post("/api/sessions")
def start_session(req: StartSessionRequest) -> dict:
    path = _FICHAS_DIR / f"{req.ficha_id}.yaml"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Ficha não encontrada")

    ficha = load_ficha(path)
    timer = SessionTimer(req.timer_minutes) if req.timer_minutes > 0 else None
    session_id = str(uuid.uuid4())

    state = SessionState(ficha=ficha, agent=PatientAgent(ficha), timer=timer)
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


@app.post("/api/sessions/{session_id}/message")
async def send_message(session_id: str, req: MessageRequest) -> dict:
    import traceback
    try:
        state = _sessions.get(session_id)
        if not state:
            state = _load_session(session_id)
            if not state:
                raise HTTPException(status_code=404, detail="Sessão não encontrada")
            _sessions[session_id] = state

        reply = await state.agent.respond_async(req.content)
        _persist_session(session_id, state)
        return {"content": reply}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e} | {traceback.format_exc()}")


@app.post("/api/sessions/{session_id}/supervise")
async def supervise(session_id: str):
    state = _sessions.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    if not state.agent.history:
        raise HTTPException(status_code=400, detail="Nenhuma conversa para supervisionar")

    supervisor = SupervisorAgent()
    approach = state.approach or "TCC"

    async def generate():
        full = ""
        async for token in supervisor.supervise_stream(state.ficha, state.agent.history, approach):
            full += token
            yield {"data": json.dumps({"type": "token", "content": token})}
        state.last_supervision = full
        yield {"data": json.dumps({"type": "done"})}

    return EventSourceResponse(generate())


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str) -> dict:
    state = _sessions.get(session_id)
    if not state:
        state = _load_session(session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        _sessions[session_id] = state

    timer_info = None
    if state.timer:
        timer_info = {
            "elapsed_str": state.timer.elapsed_str,
            "remaining_str": state.timer.remaining_str,
            "is_paused": state.timer.is_paused,
            "expired": state.timer.expired,
            "duration_minutes": state.timer.duration_minutes,
        }

    return {
        "session_id": session_id,
        "ficha_id": state.ficha.id,
        "nome": state.ficha.apresentacao.nome_ficticio,
        "nivel": state.ficha.nivel_dificuldade,
        "turn_count": len(state.agent.history) // 2,
        "timer": timer_info,
        "approaches": list(APPROACHES.keys()),
    }


@app.post("/api/sessions/{session_id}/timer/toggle")
def toggle_timer(session_id: str) -> dict:
    state = _sessions.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    if not state.timer:
        raise HTTPException(status_code=404, detail="Timer não configurado")
    paused = state.timer.toggle()
    return {"is_paused": paused, "elapsed_str": state.timer.elapsed_str}


@app.post("/api/sessions/{session_id}/timer/start")
def start_timer(session_id: str) -> dict:
    """Inicia o timer com duration padrão (30 min) se ainda não existir."""
    state = _sessions.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    if not state.timer:
        state.timer = SessionTimer(30)  # default 30 min
    if state.timer.is_paused:
        state.timer.toggle()
    timer_info = {
        "elapsed_str": state.timer.elapsed_str,
        "remaining_str": state.timer.remaining_str,
        "is_paused": state.timer.is_paused,
        "expired": state.timer.expired,
        "duration_minutes": state.timer.duration_minutes,
    }
    return {"timer": timer_info}


@app.post("/api/sessions/{session_id}/rubric")
def get_rubric(session_id: str, req: SuperviseRequest) -> dict:
    state = _sessions.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    if not state.agent.history:
        raise HTTPException(status_code=400, detail="Nenhuma conversa para avaliar")

    supervisor = SupervisorAgent()
    dimensoes = supervisor.get_rubrica(state.ficha, state.agent.history, req.approach)
    return {
        "approach": req.approach,
        "dimensoes": [
            {"nome": d.nome, "score": d.score, "justificativa": d.justificativa}
            for d in dimensoes
        ],
    }


@app.delete("/api/sessions/{session_id}")
def end_session(session_id: str) -> dict:
    state = _sessions.pop(session_id, None)
    if not state:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    turns = len(state.agent.history) // 2
    duration = int(state.timer.elapsed_seconds) if state.timer else 0
    save_session(state.ficha.id, state.agent.history, duration_seconds=duration)
    return {"turns": turns}


@app.post("/api/sessions/{session_id}/supervise-preview")
async def supervise_preview(session_id: str, req: SupervisePreviewRequest):
    """Supervisão em tempo real — aceita histórico diretamente do frontend.
    Modos:
      - realtime: últimas 2 trocas (4 mensagens)
      - session: toda a conversa
      - last3: últimas 3 trocas (6 mensagens)
    """
    state = _sessions.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    if not req.history:
        raise HTTPException(status_code=400, detail="Nenhuma mensagem para supervisionar")

    supervisor = SupervisorAgent()

    async def generate():
        full = ""
        async for token in supervisor.supervise_stream(state.ficha, req.history, req.approach):
            full += token
            yield {"data": json.dumps({"type": "token", "content": token})}
        yield {"data": json.dumps({"type": "done"})}

    return EventSourceResponse(generate())
    """Streaming supervision that saves to DB on completion."""
    state = _sessions.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    if not state.agent.history:
        raise HTTPException(status_code=400, detail="Nenhuma conversa para supervisionar")

    supervisor = SupervisorAgent()

    async def generate():
        full = ""
        async for token in supervisor.supervise_stream(state.ficha, state.agent.history, req.approach):
            full += token
            yield {"data": json.dumps({"type": "token", "content": token})}

        # Busca rubrica e salva tudo
        try:
            rubrica = supervisor.get_rubrica(state.ficha, state.agent.history, req.approach)
            scores = [{"nome": d.nome, "score": d.score, "justificativa": d.justificativa} for d in rubrica]
        except Exception:
            scores = []

        session_db_id = save_session(
            state.ficha.id, state.agent.history,
            duration_seconds=int(state.timer.elapsed_seconds) if state.timer else 0,
        )
        save_supervision(session_db_id, req.approach, full, rubric_scores=scores)
        yield {"data": json.dumps({"type": "done", "rubric": scores})}

    return EventSourceResponse(generate())


@app.get("/api/dashboard")
def dashboard() -> dict:
    return get_dashboard()
