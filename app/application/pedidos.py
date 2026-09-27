from sqlalchemy.orm import Session

from app.domain.enums import CanalPedido, StatusPedido
from app.domain.exceptions import EstoqueInsuficienteError, ProdutoIndisponivelError
from app.infrastructure.db.models import ItemPedido, Pedido
from app.infrastructure.db.repositories.estoque_repository import EstoqueRepository
from app.infrastructure.db.repositories.pedido_repository import PedidoRepository
from app.infrastructure.db.repositories.produto_repository import ProdutoRepository


def criar_pedido(
    db: Session,
    cliente_id: int,
    unidade_id: int,
    canal_pedido: CanalPedido,
    itens: list[dict],
) -> Pedido:
    produto_repo = ProdutoRepository(db)
    estoque_repo = EstoqueRepository(db)

    pedido = Pedido(cliente_id=cliente_id, unidade_id=unidade_id, canal_pedido=canal_pedido)

    for item in itens:
        produto_id = item["produto_id"]
        quantidade = item["quantidade"]

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

        pedido.adicionar_item(
            ItemPedido(produto_id=produto.id, quantidade=quantidade, preco_unitario=produto.preco)
        )

    pedido.valor_total = pedido.calcular_total()
    return PedidoRepository(db).criar(pedido)


def atualizar_status_pedido(db: Session, pedido: Pedido, novo_status: StatusPedido) -> Pedido:
    pedido.avancar_status(novo_status)
    return PedidoRepository(db).salvar(pedido)


def cancelar_pedido(db: Session, pedido: Pedido) -> Pedido:
    pedido.cancelar()
    return PedidoRepository(db).salvar(pedido)
