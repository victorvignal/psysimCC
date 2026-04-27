import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        return None
    from supabase import create_client
    _client = create_client(url, key)
    return _client


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

    fichas_dir = Path(__file__).parent.parent / "fichas" / "validated"
    ficha_nomes: dict[str, str] = {}
    try:
        from src.ficha_loader import load_ficha
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


def _empty_dashboard() -> dict:
    return {
        "stats": {"sessions": 0, "minutes": 0, "feedbacks": 0, "patients": 0},
        "recent_sessions": [],
        "progress": {},
    }
