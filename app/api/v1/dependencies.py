from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.domain.enums import PerfilUsuario
from app.infrastructure.db.models import Usuario, Pedido
from app.infrastructure.db.repositories.usuario_repository import UsuarioRepository
from app.infrastructure.db.session import get_db
from app.infrastructure.security.jwt import decodificar_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_usuario(
    credenciais: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou expiradas.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credenciais is None:
        raise credenciais_invalidas

    try:
        payload = decodificar_access_token(credenciais.credentials)
    except JWTError:
        raise credenciais_invalidas

    if payload.get("type") != "access" or payload.get("sub") is None:
        raise credenciais_invalidas

    usuario = UsuarioRepository(db).obter_por_id(int(payload["sub"]))
    if usuario is None or not usuario.ativo:
        raise credenciais_invalidas

    return usuario


def exigir_perfis(*perfis_permitidos: PerfilUsuario):
    def dependencia(usuario: Usuario = Depends(get_current_usuario)) -> Usuario:
        if usuario.role not in perfis_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para executar esta ação.",
            )
        return usuario

    return dependencia


_PERFIS_VINCULADOS_A_UNIDADE = (PerfilUsuario.ATENDENTE, PerfilUsuario.COZINHA, PerfilUsuario.GERENTE)


def verificar_acesso_unidade(usuario: Usuario, unidade_id: int) -> None:
    """Staff vinculado a uma unidade (ATENDENTE/COZINHA/GERENTE) só acessa a própria; ADMIN acessa qualquer uma."""
    if usuario.role in _PERFIS_VINCULADOS_A_UNIDADE and usuario.unidade_id != unidade_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito à sua própria unidade.",
        )


def verificar_acesso_pedido(usuario: Usuario, pedido: Pedido) -> None:
    """CLIENTE só acessa os próprios pedidos; staff, os da própria unidade; ADMIN, qualquer um."""
    if usuario.role == PerfilUsuario.ADMIN:
        return
    if usuario.role == PerfilUsuario.CLIENTE:
        if pedido.cliente_id != usuario.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito ao próprio pedido."
            )
        return
    if pedido.unidade_id != usuario.unidade_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito à sua própria unidade."
        )