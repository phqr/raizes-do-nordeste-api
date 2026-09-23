from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class ProdutoCreate(BaseModel):
    nome: str
    preco: Decimal = Field(gt=0)
    categoria: str
    sazonal: bool = False


class ProdutoUpdate(BaseModel):
    nome: Optional[str] = None
    preco: Optional[Decimal] = Field(default=None, gt=0)
    categoria: Optional[str] = None
    sazonal: Optional[bool] = None


class ProdutoResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    nome: str
    preco: Decimal
    categoria: str
    sazonal: bool
    ativo: bool
