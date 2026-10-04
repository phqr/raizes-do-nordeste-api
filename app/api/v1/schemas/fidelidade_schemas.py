from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.domain.enums import TipoConsentimento, TipoMovimentoFidelidade


class ConsentimentoFidelidadeRequest(BaseModel):
    aceito: bool


class ConsentimentoResponse(BaseModel):
    model_config = {"from_attributes": True}

    tipo: TipoConsentimento
    aceito: bool
    data_consentimento: datetime


class SaldoFidelidadeResponse(BaseModel):
    pontos: int
    valor_em_reais: Decimal
    consentimento_ativo: bool


class ResgatePontosRequest(BaseModel):
    pedido_id: int
    pontos: int = Field(gt=0, le=100_000)
