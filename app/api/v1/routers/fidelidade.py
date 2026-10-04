from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import exigir_perfis, verificar_acesso_pedido
from app.api.v1.schemas.fidelidade_schemas import (
    ConsentimentoFidelidadeRequest,
    ConsentimentoResponse,
    ResgatePontosRequest,
    SaldoFidelidadeResponse,
)
from app.api.v1.schemas.pedido_schemas import PedidoResponse
from app.application.registrar_consentimento import registrar_consentimento
from app.application.resgatar_pontos import resgatar_pontos
from app.domain.enums import PerfilUsuario, TipoConsentimento
from app.domain.exceptions import ResgateNaoPermitidoError
from app.infrastructure.db.models import Usuario
from app.infrastructure.db.repositories.fidelidade_repository import FidelidadeRepository
from app.infrastructure.db.repositories.pedido_repository import PedidoRepository
from app.infrastructure.db.repositories.usuario_repository import ConsentimentoRepository
from app.infrastructure.db.session import get_db

router = APIRouter(prefix="/fidelidade", tags=["fidelidade"])

apenas_cliente = exigir_perfis(PerfilUsuario.CLIENTE)


@router.post(
    "/consentimento", response_model=ConsentimentoResponse, status_code=status.HTTP_201_CREATED
)
def registrar_consentimento_fidelidade(
    dados: ConsentimentoFidelidadeRequest,
    db: Session = Depends(get_db),
    cliente: Usuario = Depends(apenas_cliente),
):
    return registrar_consentimento(db, cliente.id, TipoConsentimento.FIDELIDADE, dados.aceito)


@router.get("/saldo", response_model=SaldoFidelidadeResponse)
def consultar_saldo(
    db: Session = Depends(get_db),
    cliente: Usuario = Depends(apenas_cliente)
):
    saldo = FidelidadeRepository(db).obter_saldo_fidelidade(cliente.id)
    pontos = saldo.pontos_atuais if saldo else 0
    valor_em_reais = saldo.valor_em_reais() if saldo else Decimal("0")
    consentimento_ativo = ConsentimentoRepository(db).consentimento_ativo(
        cliente.id, TipoConsentimento.FIDELIDADE
    )
    return SaldoFidelidadeResponse(
        pontos=pontos,
        valor_em_reais=valor_em_reais,
        consentimento_ativo=consentimento_ativo,
    )


@router.post("/resgate", response_model=PedidoResponse)
def resgatar(
    dados: ResgatePontosRequest,
    db: Session = Depends(get_db),
    cliente: Usuario = Depends(apenas_cliente),
):
    pedido = PedidoRepository(db).obter_por_id(dados.pedido_id)
    if pedido is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado.")

    verificar_acesso_pedido(cliente, pedido)

    try:
        return resgatar_pontos(db, pedido, dados.pontos)
    except ResgateNaoPermitidoError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
