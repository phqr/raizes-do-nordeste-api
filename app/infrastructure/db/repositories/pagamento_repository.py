from typing import Optional

from sqlalchemy.orm import Session

from app.infrastructure.db.models import Pagamento


class PagamentoRepository:
    def __init__(self, db: Session):
        self.db = db

    def obter_por_id(self, pagamento_id: int) -> Optional[Pagamento]:
        return self.db.get(Pagamento, pagamento_id)

    def obter_por_chave(self, chave_idempotencia: str) -> Optional[Pagamento]:
        return (
            self.db.query(Pagamento)
            .filter(Pagamento.chave_idempotencia == chave_idempotencia)
            .first()
        )

    def salvar(self, pagamento: Pagamento) -> Pagamento:
        self.db.add(pagamento)
        self.db.commit()
        self.db.refresh(pagamento)
        return pagamento
