import os
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
    metadata: dict[str, Any] | None = None,
) -> str | None:
    client = _get_client()
    if not client:
        return None
    result = (
        client.table("sessions")
        .insert({"ficha_id": ficha_id, "turns": turns, "metadata": metadata or {}})
        .execute()
    )
    return result.data[0]["id"] if result.data else None


def save_supervision(session_id: str | None, approach: str, feedback: str) -> None:
    client = _get_client()
    if not client:
        return
    client.table("supervisions").insert(
        {"session_id": session_id, "approach": approach, "feedback": feedback}
    ).execute()
