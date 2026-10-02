from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import (
    exigir_perfis,
    get_current_usuario,
    verificar_acesso_pedido,
    verificar_acesso_unidade,
)
from app.api.v1.schemas.pedido_schemas import (
    AtualizarStatusRequest,
    PedidoCreate,
    PedidoResponse,
)
from app.application.pedidos import atualizar_status_pedido, cancelar_pedido, criar_pedido
from app.domain.enums import CanalPedido, PerfilUsuario, StatusPedido
from app.domain.exceptions import (
    EstoqueInsuficienteError,
    PedidoNaoPodeSerCanceladoError,
    ProdutoIndisponivelError,
    TransicaoStatusInvalidaError,
)
from app.infrastructure.db.models import Usuario
from app.infrastructure.db.repositories.pedido_repository import PedidoRepository
from app.infrastructure.db.repositories.unidade_repository import UnidadeRepository
from app.infrastructure.db.repositories.usuario_repository import UsuarioRepository
from app.infrastructure.db.session import get_db

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


@router.post("", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
def criar_pedido_endpoint(
    dados: PedidoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(exigir_perfis(PerfilUsuario.CLIENTE, PerfilUsuario.ATENDENTE)),
):
    if usuario.role == PerfilUsuario.CLIENTE:
        cliente_id = usuario.id
    else:
        verificar_acesso_unidade(usuario, dados.unidade_id)
        if dados.cliente_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="cliente_id é obrigatório para pedidos criados por atendente.",
            )
        cliente = UsuarioRepository(db).obter_por_id(dados.cliente_id)
        if cliente is None or cliente.role != PerfilUsuario.CLIENTE or not cliente.ativo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado."
            )
        cliente_id = cliente.id

    unidade = UnidadeRepository(db).obter_por_id(dados.unidade_id)
    if unidade is None or not unidade.ativo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")

    try:
        return criar_pedido(
            db,
            cliente_id=cliente_id,
            unidade_id=dados.unidade_id,
            canal_pedido=dados.canal_pedido,
            itens=[item.model_dump() for item in dados.itens],
        )
    except ProdutoIndisponivelError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except EstoqueInsuficienteError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("", response_model=list[PedidoResponse])
def listar_pedidos(
    canal_pedido: Optional[CanalPedido] = Query(default=None, alias="canalPedido"),
    status_filtro: Optional[StatusPedido] = Query(default=None, alias="status"),
    unidade_id: Optional[int] = None,
    cliente_id: Optional[int] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
):
    if usuario.role == PerfilUsuario.CLIENTE:
        cliente_id = usuario.id
    elif usuario.role in (PerfilUsuario.ATENDENTE, PerfilUsuario.COZINHA, PerfilUsuario.GERENTE):
        if usuario.unidade_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Usuário sem unidade vinculada."
            )
        unidade_id = usuario.unidade_id

    return PedidoRepository(db).listar(
        page=page,
        limit=limit,
        canal_pedido=canal_pedido,
        status=status_filtro,
        unidade_id=unidade_id,
        cliente_id=cliente_id,
    )


@router.get("/{pedido_id}", response_model=PedidoResponse)
def obter_pedido(
    pedido_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_usuario)
):
    pedido = PedidoRepository(db).obter_por_id(pedido_id)
    if pedido is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado.")

    verificar_acesso_pedido(usuario, pedido)
    return pedido


@router.put("/{pedido_id}/status", response_model=PedidoResponse)
def atualizar_status(
    pedido_id: int,
    dados: AtualizarStatusRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        exigir_perfis(PerfilUsuario.COZINHA, PerfilUsuario.GERENTE, PerfilUsuario.ADMIN)
    ),
):
    pedido = PedidoRepository(db).obter_por_id(pedido_id)
    if pedido is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado.")

    verificar_acesso_pedido(usuario, pedido)

    try:
        return atualizar_status_pedido(db, pedido, dados.status)
    except TransicaoStatusInvalidaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("/{pedido_id}/cancelar", response_model=PedidoResponse)
def cancelar(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        exigir_perfis(
            PerfilUsuario.CLIENTE,
            PerfilUsuario.ATENDENTE,
            PerfilUsuario.GERENTE,
            PerfilUsuario.ADMIN,
        )
    ),
):
    pedido = PedidoRepository(db).obter_por_id(pedido_id)
    if pedido is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado.")

    verificar_acesso_pedido(usuario, pedido)

    try:
        return cancelar_pedido(db, pedido)
    except PedidoNaoPodeSerCanceladoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
