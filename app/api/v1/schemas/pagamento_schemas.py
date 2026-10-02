from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.domain.enums import StatusPagamento


class SolicitarPagamentoRequest(BaseModel):
    pedido_id: int
    chave_idempotencia: str = Field(min_length=8, max_length=64)
    simular_timeout: bool = Field(
        default=False, description="Só no mock: faz o gateway não responder (timeout)."
    )


class CallbackPagamentoRequest(BaseModel):
    pagamento_id: int
    resultado: Literal[StatusPagamento.APROVADO, StatusPagamento.RECUSADO]


class PagamentoResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    pedido_id: int
    status: StatusPagamento
    valor: Decimal
    chave_idempotencia: str
    tentativas: int
    motivo: Optional[str]
