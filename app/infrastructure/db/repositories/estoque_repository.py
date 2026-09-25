from typing import Optional

from sqlalchemy.orm import Session

from app.infrastructure.db.models import EstoqueUnidade, Produto


class EstoqueRepository:
    def __init__(self, db: Session):
        self.db = db

    def obter(self, produto_id: int, unidade_id: int) -> Optional[EstoqueUnidade]:
        return (
            self.db.query(EstoqueUnidade)
            .filter(EstoqueUnidade.produto_id == produto_id, EstoqueUnidade.unidade_id == unidade_id)
            .first()
        )

    def obter_ou_criar(self, produto_id: int, unidade_id: int) -> EstoqueUnidade:
        estoque = self.obter(produto_id, unidade_id)
        if estoque is None:
            estoque = EstoqueUnidade(produto_id=produto_id, unidade_id=unidade_id, quantidade=0)
            self.db.add(estoque)
            self.db.commit()
            self.db.refresh(estoque)
        return estoque

    def listar_por_unidade(self, unidade_id: int) -> list[EstoqueUnidade]:
        return self.db.query(EstoqueUnidade).filter(EstoqueUnidade.unidade_id == unidade_id).all()

    def salvar(self, estoque: EstoqueUnidade) -> EstoqueUnidade:
        self.db.commit()
        self.db.refresh(estoque)
        return estoque

    def listar_cardapio_unidade(self, unidade_id: int) -> list[Produto]:
        return (
            self.db.query(Produto)
            .join(EstoqueUnidade, EstoqueUnidade.produto_id == Produto.id)
            .filter(
                EstoqueUnidade.unidade_id == unidade_id,
                EstoqueUnidade.quantidade > 0,
                Produto.ativo.is_(True),
            )
            .order_by(Produto.nome)
            .all()
        )
