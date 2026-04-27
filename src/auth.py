import os
from typing import Optional

import jwt
from jwt import PyJWKClient
from fastapi import Header, HTTPException

_jwks_client: Optional[PyJWKClient] = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
        if not url:
            raise HTTPException(status_code=500, detail="SUPABASE_URL não configurado")
        _jwks_client = PyJWKClient(f"{url}/auth/v1/.well-known/jwks.json")
    return _jwks_client


def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """Extrai e valida o JWT do Supabase. Suporta HS256 e RS256."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Não autenticado")

    token = authorization.split(" ", 1)[1].strip()

    try:
        header = jwt.get_unverified_header(token)
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Token malformado")

    alg = header.get("alg", "HS256")

    try:
        if alg == "HS256":
            secret = (os.getenv("SUPABASE_JWT_SECRET") or "").strip()
            if not secret:
                raise HTTPException(status_code=500, detail="SUPABASE_JWT_SECRET não configurado")
            payload = jwt.decode(
                token, secret,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        else:
            signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token, signing_key.key,
                algorithms=["RS256"],
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
