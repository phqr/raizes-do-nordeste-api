from typing import Optional

from sqlalchemy.orm import Session

from app.infrastructure.db.models import Unidade


class UnidadeRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, page: int, limit: int) -> list[Unidade]:
        return (
            self.db.query(Unidade)
            .order_by(Unidade.nome, Unidade.id)
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

    def obter_por_id(self, unidade_id: int) -> Optional[Unidade]:
        return self.db.get(Unidade, unidade_id)

    def criar(self, unidade: Unidade) -> Unidade:
        self.db.add(unidade)
        self.db.commit()
        self.db.refresh(unidade)
        return unidade

    def atualizar(self, unidade: Unidade) -> Unidade:
        self.db.commit()
        self.db.refresh(unidade)
        return unidade
