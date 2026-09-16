import hashlib
import secrets
from datetime import datetime, timedelta

from jose import jwt

from app.core.config import settings


def criar_access_token(usuario_id: int, role: str) -> str:
    expira_em = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(usuario_id), "role": role, "type": "access", "exp": expira_em}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decodificar_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def gerar_refresh_token() -> tuple[str, str, datetime]:
    token = secrets.token_urlsafe(32)
    token_hash = hash_refresh_token(token)
    expira_em = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    return token, token_hash, expira_em
