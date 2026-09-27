from typing import Optional

from sqlalchemy.orm import Session

from app.domain.enums import CanalPedido, StatusPedido
from app.infrastructure.db.models import Pedido


class PedidoRepository:
    def __init__(self, db: Session):
        self.db = db

    def obter_por_id(self, pedido_id: int) -> Optional[Pedido]:
        return self.db.get(Pedido, pedido_id)

    def criar(self, pedido: Pedido) -> Pedido:
        self.db.add(pedido)
        self.db.commit()
        self.db.refresh(pedido)
        return pedido

    def salvar(self, pedido: Pedido) -> Pedido:
        self.db.commit()
        self.db.refresh(pedido)
        return pedido

    def listar(
        self,
        canal_pedido: Optional[CanalPedido] = None,
        status: Optional[StatusPedido] = None,
        unidade_id: Optional[int] = None,
        cliente_id: Optional[int] = None,
    ) -> list[Pedido]:
        query = self.db.query(Pedido)
        if canal_pedido is not None:
            query = query.filter(Pedido.canal_pedido == canal_pedido)
        if status is not None:
            query = query.filter(Pedido.status == status)
        if unidade_id is not None:
            query = query.filter(Pedido.unidade_id == unidade_id)
        if cliente_id is not None:
            query = query.filter(Pedido.cliente_id == cliente_id)
        return query.order_by(Pedido.criado_em.desc()).all()
