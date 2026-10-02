from decimal import Decimal


class GatewayIndisponivelError(Exception):
    pass


# O resultado (APROVADO/RECUSADO) chega depois, pelo callback; a chave evita cobrança dupla no gateway.
def enviar_cobranca(chave_idempotencia: str, valor: Decimal, simular_timeout: bool = False) -> None:
    if simular_timeout:
        raise GatewayIndisponivelError("Tempo esgotado ao contatar o gateway de pagamento.")
