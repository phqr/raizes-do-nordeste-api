from typing import Optional

from pydantic import BaseModel

from app.domain.enums import TipoOperacaoUnidade


class UnidadeCreate(BaseModel):
    nome: str
    endereco: str
    tipo_operacao: TipoOperacaoUnidade


class UnidadeUpdate(BaseModel):
    nome: Optional[str] = None
    endereco: Optional[str] = None
    tipo_operacao: Optional[TipoOperacaoUnidade] = None
    ativo: Optional[bool] = None


class UnidadeResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    nome: str
    endereco: str
    tipo_operacao: TipoOperacaoUnidade
    ativo: bool
