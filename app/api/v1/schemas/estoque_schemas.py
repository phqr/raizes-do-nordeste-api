from pydantic import BaseModel, Field


class EntradaEstoqueRequest(BaseModel):
    produto_id: int
    unidade_id: int
    quantidade: int = Field(gt=0)


class EstoqueResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    produto_id: int
    unidade_id: int
    quantidade: int
