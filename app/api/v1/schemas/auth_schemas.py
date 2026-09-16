from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.domain.enums import PerfilUsuario


class CadastroClienteRequest(BaseModel):
    nome: str
    email: EmailStr
    senha: str = Field(min_length=8)
    cpf: Optional[str] = None
    data_nascimento: Optional[date] = None
    aceite_lgpd: bool


class CadastroUsuarioInternoRequest(BaseModel):
    nome: str
    email: EmailStr
    senha: str = Field(min_length=8)
    role: PerfilUsuario
    unidade_id: Optional[int] = None


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UsuarioResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    nome: str
    email: EmailStr
    role: PerfilUsuario
    unidade_id: Optional[int]
    ativo: bool
