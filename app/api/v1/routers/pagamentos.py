import secrets
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import exigir_perfis, verificar_acesso_pedido
from app.api.v1.schemas.pagamento_schemas import (
    CallbackPagamentoRequest,
    PagamentoResponse,
    SolicitarPagamentoRequest,
)
from app.application.pagamento import confirmar_pagamento, solicitar_pagamento
from app.core.config import settings
from app.domain.enums import PerfilUsuario
from app.domain.exceptions import PagamentoNaoPermitidoError
from app.infrastructure.db.models import Usuario
from app.infrastructure.db.repositories.pagamento_repository import PagamentoRepository
from app.infrastructure.db.repositories.pedido_repository import PedidoRepository
from app.infrastructure.db.session import get_db

router = APIRouter(prefix="/pagamentos", tags=["pagamentos"])


def _validar_segredo_gateway(x_gateway_secret: Optional[str] = Header(default=None)) -> None:
    # Sem essa verificação, qualquer cliente poderia aprovar o próprio pagamento chamando o callback.
    if x_gateway_secret is None or not secrets.compare_digest(
        x_gateway_secret.encode(), settings.gateway_webhook_secret.encode()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Callback do gateway não autenticado."
        )


@router.post("", response_model=PagamentoResponse, status_code=status.HTTP_202_ACCEPTED)
def solicitar(
    dados: SolicitarPagamentoRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(exigir_perfis(PerfilUsuario.CLIENTE, PerfilUsuario.ATENDENTE)),
):
    pedido = PedidoRepository(db).obter_por_id(dados.pedido_id)
    if pedido is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado.")

    verificar_acesso_pedido(usuario, pedido)

    try:
        return solicitar_pagamento(
            db, pedido, dados.chave_idempotencia, simular_timeout=dados.simular_timeout
        )
    except PagamentoNaoPermitidoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post(
    "/callback",
    response_model=PagamentoResponse,
    dependencies=[Depends(_validar_segredo_gateway)],
)
def callback(dados: CallbackPagamentoRequest, db: Session = Depends(get_db)):
    pagamento = PagamentoRepository(db).obter_por_id(dados.pagamento_id)
    if pagamento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pagamento não encontrado."
        )

    try:
        return confirmar_pagamento(db, pagamento, dados.resultado)
    except PagamentoNaoPermitidoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
