from sqlalchemy.orm import Session

from app.domain.enums import (
    StatusPagamento,
    StatusPedido,
    TipoConsentimento,
    TipoMovimentoFidelidade,
)
from app.domain.exceptions import ResgateNaoPermitidoError
from app.infrastructure.db.models import VALOR_DO_PONTO_FIDELIDADE, Pedido
from app.infrastructure.db.repositories.fidelidade_repository import FidelidadeRepository
from app.infrastructure.db.repositories.pedido_repository import PedidoRepository
from app.infrastructure.db.repositories.usuario_repository import ConsentimentoRepository


def resgatar_pontos(db: Session, pedido: Pedido, pontos: int) -> Pedido:
    participa_programa_fidelidade = ConsentimentoRepository(db).consentimento_ativo(
        pedido.cliente_id, TipoConsentimento.FIDELIDADE
    )
    if not participa_programa_fidelidade:
        raise ResgateNaoPermitidoError("Cliente não participa do programa de fidelidade.")
    if pedido.status != StatusPedido.AGUARDANDO_PAGAMENTO:
        raise ResgateNaoPermitidoError("Só é possível resgatar pontos em pedido aguardando pagamento.")
    if pedido.pagamento is not None and pedido.pagamento.status == StatusPagamento.PENDENTE:
        raise ResgateNaoPermitidoError("O pagamento deste pedido já foi solicitado.")
    if pedido.desconto_fidelidade > 0:
        raise ResgateNaoPermitidoError("Este pedido já recebeu desconto de fidelidade.")

    repo = FidelidadeRepository(db)
    saldo_fidelidade = repo.obter_saldo_fidelidade(pedido.cliente_id)
    if saldo_fidelidade is None or not saldo_fidelidade.saldo_suficiente(pontos):
        raise ResgateNaoPermitidoError("Saldo de pontos insuficiente.")

    pedido.aplicar_desconto_fidelidade(pontos * VALOR_DO_PONTO_FIDELIDADE)
    saldo_fidelidade.debitar(pontos)
    repo.registrar_movimentacao(pedido.cliente_id, pedido.id, TipoMovimentoFidelidade.RESGATE, pontos)
    return PedidoRepository(db).salvar(pedido)
