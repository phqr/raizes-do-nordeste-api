from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.domain.enums import CanalPedido, StatusPedido


class ItemPedidoCreate(BaseModel):
    produto_id: int
    quantidade: int = Field(gt=0)


class PedidoCreate(BaseModel):
    unidade_id: int
    canal_pedido: CanalPedido
    cliente_id: Optional[int] = None
    itens: list[ItemPedidoCreate] = Field(min_length=1)


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
    canal_pedido: CanalPedido
    status: StatusPedido
    valor_total: Decimal
    desconto_fidelidade: Decimal
    itens: list[ItemPedidoResponse]


class AtualizarStatusRequest(BaseModel):
    status: StatusPedido
