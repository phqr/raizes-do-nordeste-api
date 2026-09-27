class EmailJaCadastradoError(Exception):
    pass


class CredenciaisInvalidasError(Exception):
    pass


class RefreshTokenInvalidoError(Exception):
    pass


class EstoqueInsuficienteError(Exception):
    pass


class ProdutoIndisponivelError(Exception):
    pass


class TransicaoStatusInvalidaError(Exception):
    pass


class PedidoNaoPodeSerCanceladoError(Exception):
    pass
