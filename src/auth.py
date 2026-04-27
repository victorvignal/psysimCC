import os
from typing import Optional

import httpx
from fastapi import Header, HTTPException

_SUPABASE_URL = ""


def _supabase_url() -> str:
    global _SUPABASE_URL
    if not _SUPABASE_URL:
        _SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    return _SUPABASE_URL


async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """Valida o JWT chamando GET /auth/v1/user no Supabase. Async, sem bloquear o event loop."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Não autenticado")

    token = authorization.split(" ", 1)[1].strip()
    url = _supabase_url()

    if not url:
        raise HTTPException(status_code=500, detail="SUPABASE_URL não configurado")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{url}/auth/v1/user",
                headers={"Authorization": f"Bearer {token}"},
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=401, detail="Timeout ao verificar token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Erro ao verificar token: {e}")

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    user_id = resp.json().get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token sem user_id")

    return str(user_id)
