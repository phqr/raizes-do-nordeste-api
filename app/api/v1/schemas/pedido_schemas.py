from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.domain.enums import CanalPedido, StatusPedido


class ItemPedidoCreate(BaseModel):
    produto_id: int
    quantidade: int = Field(gt=0, le=100)


class PedidoCreate(BaseModel):
    # O contrato do enunciado usa `canalPedido`; `canal_pedido` continua aceito.
    model_config = {"populate_by_name": True}

    unidade_id: int
    canal_pedido: CanalPedido = Field(alias="canalPedido")
    cliente_id: Optional[int] = None
    itens: list[ItemPedidoCreate] = Field(min_length=1, max_length=50)


class ItemPedidoResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    produto_id: int
    quantidade: int
    preco_unitario: Decimal


class PedidoResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    cliente_id: int
    unidade_id: int
    canal_pedido: CanalPedido = Field(serialization_alias="canalPedido")
    status: StatusPedido
    valor_total: Decimal
    desconto_fidelidade: Decimal
    itens: list[ItemPedidoResponse]


class AtualizarStatusRequest(BaseModel):
    status: StatusPedido
