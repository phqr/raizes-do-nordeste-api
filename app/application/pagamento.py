from sqlalchemy.orm import Session

from app.domain.enums import StatusPagamento, StatusPedido
from app.infrastructure.db.models import Pagamento, Pedido
from app.domain.exceptions import PagamentoNaoPermitidoError
from app.infrastructure.db.repositories.pagamento_repository import PagamentoRepository
from app.infrastructure.payment.mock_gateway import GatewayIndisponivelError, enviar_cobranca

MAX_TENTATIVAS_GATEWAY = 3


def solicitar_pagamento(
    db: Session, pedido: Pedido, chave_idempotencia: str, simular_timeout: bool = False
) -> Pagamento:
    repo = PagamentoRepository(db)
    pagamento = pedido.pagamento

    # Reenvio da mesma solicitação: devolve o que já foi registrado, sem cobrar de novo (RF23).
    if pagamento is not None and pagamento.ja_processado(chave_idempotencia):
        return pagamento
    if repo.obter_por_chave(chave_idempotencia) is not None:
        raise PagamentoNaoPermitidoError("Chave de idempotência já usada em outro pedido.")
    if pedido.status != StatusPedido.AGUARDANDO_PAGAMENTO:
        raise PagamentoNaoPermitidoError(
            f"Pedido no status {pedido.status.value} não aceita pagamento."
        )

    if pagamento is None:
        pagamento = Pagamento(pedido=pedido, tentativas=0)
    pagamento.solicitar(chave_idempotencia, pedido.valor_total)

    ultimo_erro = ""
    for _ in range(MAX_TENTATIVAS_GATEWAY):
        pagamento.tentativas += 1
        try:
            enviar_cobranca(chave_idempotencia, pagamento.valor, simular_timeout)
            break
        except GatewayIndisponivelError as exc:
            ultimo_erro = str(exc)
    else:
        # Só chega aqui se nenhuma tentativa deu `break`, ou seja, todas falharam.
        pagamento.registrar_falha(f"{ultimo_erro} ({MAX_TENTATIVAS_GATEWAY} tentativas)")

    return repo.salvar(pagamento)


def confirmar_pagamento(db: Session, pagamento: Pagamento, resultado: StatusPagamento) -> Pagamento:
    # Gateways reenviam callbacks; o mesmo resultado repetido não muda nada.
    if pagamento.status == resultado:
        return pagamento

    pagamento.registrar_callback(resultado)
    if resultado == StatusPagamento.APROVADO:
        pedido = pagamento.pedido
        if pedido.status == StatusPedido.CANCELADO:
            pagamento.estornar("Pagamento aprovado após o cancelamento do pedido; valor estornado.")
        else:
            pedido.confirmar_pagamento()

    return PagamentoRepository(db).salvar(pagamento)
