import os
from typing import Optional

import jwt
from fastapi import Header, HTTPException


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
