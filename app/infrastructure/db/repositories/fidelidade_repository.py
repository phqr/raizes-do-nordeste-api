from typing import Optional

from sqlalchemy.orm import Session

from app.domain.enums import TipoMovimentoFidelidade
from app.infrastructure.db.models import MovimentacaoFidelidade, SaldoFidelidade


class FidelidadeRepository:
    def __init__(self, db: Session):
        self.db = db

    def obter_saldo_fidelidade(self, cliente_id: int) -> Optional[SaldoFidelidade]:
        return self.db.query(SaldoFidelidade).filter(SaldoFidelidade.cliente_id == cliente_id).first()

    def obter_ou_criar_saldo(self, cliente_id: int) -> SaldoFidelidade:
        saldo = self.obter_saldo_fidelidade(cliente_id)
        if saldo is None:
            saldo = SaldoFidelidade(cliente_id=cliente_id, pontos_atuais=0)
            self.db.add(saldo)
        return saldo

    # Não faz commit: a movimentação é gravada junto com o pedido, no commit do caso de uso.
    def registrar_movimentacao(
        self, cliente_id: int, pedido_id: int, tipo: TipoMovimentoFidelidade, pontos: int
    ) -> None:
        self.db.add(
            MovimentacaoFidelidade(cliente_id=cliente_id, pedido_id=pedido_id, tipo=tipo, pontos=pontos)
        )

    def obter_movimentacao(
        self, pedido_id: int, tipo: TipoMovimentoFidelidade
    ) -> Optional[MovimentacaoFidelidade]:
        return (
            self.db.query(MovimentacaoFidelidade)
            .filter(MovimentacaoFidelidade.pedido_id == pedido_id, MovimentacaoFidelidade.tipo == tipo)
            .first()
        )

    def listar_movimentacoes(self, cliente_id: int, page: int, limit: int) -> list[MovimentacaoFidelidade]:
        return (
            self.db.query(MovimentacaoFidelidade)
            .filter(MovimentacaoFidelidade.cliente_id == cliente_id)
            .order_by(MovimentacaoFidelidade.id.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
