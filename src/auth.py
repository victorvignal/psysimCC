import os
from typing import Optional

from fastapi import Header, HTTPException
from supabase import create_client

_supabase_client = None


def _get_client():
    global _supabase_client
    if _supabase_client is None:
        url = (os.getenv("SUPABASE_URL") or "").strip()
        key = (os.getenv("SUPABASE_KEY") or "").strip()
        if not url or not key:
            return None
        _supabase_client = create_client(url, key)
    return _supabase_client


def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """Valida o JWT via Supabase Auth API. Funciona com HS256 e RS256."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Não autenticado")

    token = authorization.split(" ", 1)[1].strip()

    client = _get_client()
    if not client:
        raise HTTPException(status_code=500, detail="Supabase não configurado")

    try:
        result = client.auth.get_user(token)
        user = result.user
        if not user or not user.id:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        return str(user.id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")
