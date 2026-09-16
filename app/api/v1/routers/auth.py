from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import exigir_perfis, get_current_usuario
from app.api.v1.schemas.auth_schemas import (
    AccessTokenResponse,
    CadastroClienteRequest,
    CadastroUsuarioInternoRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
    UsuarioResponse,
)
from app.application.registrar_consentimento import registrar_consentimento
from app.domain.enums import PerfilUsuario, TipoConsentimento
from app.infrastructure.db.models import Usuario
from app.infrastructure.db.repositories.usuario_repository import (
    RefreshTokenRepository,
    UsuarioRepository,
)
from app.infrastructure.db.session import get_db
from app.infrastructure.security.hashing import hash_senha
from app.infrastructure.security.jwt import (
    criar_access_token,
    gerar_refresh_token,
    hash_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _emitir_tokens(db: Session, usuario: Usuario) -> TokenResponse:
    access_token = criar_access_token(usuario.id, usuario.role.value)
    refresh_token, token_hash, expira_em = gerar_refresh_token()
    RefreshTokenRepository(db).criar(usuario.id, token_hash, expira_em)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/registrar", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def registrar_cliente(dados: CadastroClienteRequest, db: Session = Depends(get_db)):
    repo = UsuarioRepository(db)
    if repo.obter_por_email(dados.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado.")

    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(dados.senha),
        role=PerfilUsuario.CLIENTE,
        cpf=dados.cpf,
        data_nascimento=dados.data_nascimento,
    )
    usuario = repo.criar(usuario)
    registrar_consentimento(db, usuario.id, TipoConsentimento.CADASTRO_LGPD, dados.aceite_lgpd)
    return usuario


@router.post(
    "/registrar-interno", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED
)
def registrar_usuario_interno(
    dados: CadastroUsuarioInternoRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(exigir_perfis(PerfilUsuario.GERENTE, PerfilUsuario.ADMIN)),
):
    if dados.role == PerfilUsuario.CLIENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use /auth/registrar para cadastro de clientes.",
        )

    repo = UsuarioRepository(db)
    if repo.obter_por_email(dados.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado.")

    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(dados.senha),
        role=dados.role,
        unidade_id=dados.unidade_id,
    )
    return repo.criar(usuario)


@router.post("/login", response_model=TokenResponse)
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    usuario = UsuarioRepository(db).obter_por_email(dados.email)
    if usuario is None or not usuario.autenticar(dados.senha):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos."
        )

    return _emitir_tokens(db, usuario)


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(dados: RefreshRequest, db: Session = Depends(get_db)):
    repo = RefreshTokenRepository(db)
    refresh_token = repo.obter_por_hash(hash_refresh_token(dados.refresh_token))

    if refresh_token is None or not refresh_token.valido():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido ou expirado."
        )

    usuario = UsuarioRepository(db).obter_por_id(refresh_token.usuario_id)
    if usuario is None or not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido ou expirado."
        )

    return AccessTokenResponse(access_token=criar_access_token(usuario.id, usuario.role.value))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(dados: LogoutRequest, db: Session = Depends(get_db)):
    repo = RefreshTokenRepository(db)
    refresh_token = repo.obter_por_hash(hash_refresh_token(dados.refresh_token))

    if refresh_token is not None:
        repo.revogar(refresh_token)


@router.get("/me", response_model=UsuarioResponse)
def obter_usuario_atual(usuario: Usuario = Depends(get_current_usuario)):
    return usuario
