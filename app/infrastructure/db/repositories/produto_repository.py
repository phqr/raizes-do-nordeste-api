from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.infrastructure.db.models import Produto


class ProdutoRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(
        self,
        page: int,
        limit: int,
        categoria: Optional[str] = None,
        sazonal: Optional[bool] = None,
        ativo: Optional[bool] = None,
    ) -> list[Produto]:
        query = self.db.query(Produto)
        if categoria is not None:
            query = query.filter(func.lower(Produto.categoria) == categoria.lower())
        if sazonal is not None:
            query = query.filter(Produto.sazonal == sazonal)
        if ativo is not None:
            query = query.filter(Produto.ativo == ativo)
        return (
            query.order_by(Produto.nome, Produto.id)
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

    def obter_por_id(self, produto_id: int) -> Optional[Produto]:
        return self.db.get(Produto, produto_id)

    def criar(self, produto: Produto) -> Produto:
        self.db.add(produto)
        self.db.commit()
        self.db.refresh(produto)
        return produto

    def atualizar(self, produto: Produto) -> Produto:
        self.db.commit()
        self.db.refresh(produto)
        return produto
