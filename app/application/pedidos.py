from sqlalchemy.orm import Session

from app.domain.enums import StatusPagamento
from app.domain.enums import CanalPedido, StatusPedido, TipoConsentimento, TipoMovimentoFidelidade
from app.domain.exceptions import EstoqueInsuficienteError, ProdutoIndisponivelError
from app.infrastructure.db.models import ItemPedido, Pedido
from app.infrastructure.db.repositories.estoque_repository import EstoqueRepository
from app.infrastructure.db.repositories.fidelidade_repository import FidelidadeRepository
from app.infrastructure.db.repositories.pedido_repository import PedidoRepository
from app.infrastructure.db.repositories.produto_repository import ProdutoRepository
from app.infrastructure.db.repositories.usuario_repository import ConsentimentoRepository


def _acumular_pontos(db: Session, pedido: Pedido) -> None:
    # 1 ponto por R$ 1 efetivamente gasto; sem consentimento o cliente fica fora do programa.
    consentiu = ConsentimentoRepository(db).consentimento_ativo(
        pedido.cliente_id, TipoConsentimento.FIDELIDADE
    )
    if not consentiu:
        return

    pontos = int(pedido.valor_total)

    repo = FidelidadeRepository(db)
    repo.obter_ou_criar_saldo(pedido.cliente_id).creditar(pontos)
    repo.registrar_movimentacao(pedido.cliente_id, pedido.id, TipoMovimentoFidelidade.ACUMULO, pontos)


def criar_pedido(
    db: Session,
    cliente_id: int,
    unidade_id: int,
    canal_pedido: CanalPedido,
    itens: list[dict],
) -> Pedido:
    produto_repo = ProdutoRepository(db)
    estoque_repo = EstoqueRepository(db)

    # Itens repetidos do mesmo produto viram uma linha só, e o estoque é validado pelo total.
    quantidades: dict[int, int] = {}
    for item in itens:
        quantidades[item["produto_id"]] = quantidades.get(item["produto_id"], 0) + item["quantidade"]

    # Valida todos os itens antes de mexer no estoque, para um erro no meio não deixar baixa pela metade.
    validados = []
    for produto_id, quantidade in quantidades.items():
        produto = produto_repo.obter_por_id(produto_id)
        if produto is None or not produto.ativo:
            raise ProdutoIndisponivelError(f"Produto {produto_id} indisponível.")

        estoque = estoque_repo.obter(produto_id, unidade_id)
        if estoque is None:
            raise ProdutoIndisponivelError(
                f"Produto {produto_id} indisponível na unidade {unidade_id}."
            )
        if not estoque.tem_saldo_suficiente(quantidade):
            raise EstoqueInsuficienteError(f"Estoque insuficiente para o produto {produto_id}.")

        validados.append((produto, estoque, quantidade))

    pedido = Pedido(cliente_id=cliente_id, unidade_id=unidade_id, canal_pedido=canal_pedido)
    for produto, estoque, quantidade in validados:
        estoque.dar_baixa(quantidade)
        pedido.adicionar_item(
            ItemPedido(produto_id=produto.id, quantidade=quantidade, preco_unitario=produto.preco)
        )

    pedido.valor_total = pedido.calcular_total()
    # O commit do pedido grava junto a baixa de estoque (mesma sessão/transação).
    return PedidoRepository(db).criar(pedido)


def atualizar_status_pedido(db: Session, pedido: Pedido, novo_status: StatusPedido) -> Pedido:
    pedido.avancar_status(novo_status)

    if novo_status == StatusPedido.ENTREGUE:
        _acumular_pontos(db, pedido)

    return PedidoRepository(db).salvar(pedido)


def cancelar_pedido(db: Session, pedido: Pedido) -> Pedido:
    pedido.cancelar()

    # A baixa acontece na criação do pedido, então o cancelamento devolve os itens ao estoque.
    estoque_repo = EstoqueRepository(db)
    for item in pedido.itens:
        estoque = estoque_repo.obter(item.produto_id, pedido.unidade_id)
        if estoque is not None:
            estoque.dar_entrada(item.quantidade)

    pagamento = pedido.pagamento
    if pagamento is not None and pagamento.status == StatusPagamento.APROVADO:
        pagamento.estornar("Estorno por cancelamento do pedido.")

    # Pontos resgatados como desconto voltam para o saldo do cliente.
    fidelidade_repo = FidelidadeRepository(db)
    resgate = fidelidade_repo.obter_movimentacao(pedido.id, TipoMovimentoFidelidade.RESGATE)
    if resgate is not None:
        fidelidade_repo.obter_ou_criar_saldo(pedido.cliente_id).creditar(resgate.pontos)
        fidelidade_repo.registrar_movimentacao(
            pedido.cliente_id, pedido.id, TipoMovimentoFidelidade.ESTORNO, resgate.pontos
        )

    return PedidoRepository(db).salvar(pedido)
