from datetime import date, datetime
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import (
    CanalPedido,
    PerfilUsuario,
    StatusPedido,
    TipoConsentimento,
    TipoOperacaoUnidade,
)
from app.domain.exceptions import (
    EstoqueInsuficienteError,
    PedidoNaoPodeSerCanceladoError,
    TransicaoStatusInvalidaError,
)
from app.infrastructure.db.session import Base


class Unidade(Base):
    __tablename__ = "unidades"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(sa.String, nullable=False)
    endereco: Mapped[str] = mapped_column(sa.String, nullable=False)
    tipo_operacao: Mapped[TipoOperacaoUnidade] = mapped_column(
        sa.Enum(TipoOperacaoUnidade), nullable=False
    )
    ativo: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="unidade")
    estoques: Mapped[list["EstoqueUnidade"]] = relationship(back_populates="unidade")

    def possui_produto_disponivel(self, produto_id: int) -> bool:
        return any(e.produto_id == produto_id and not e.zerado() for e in self.estoques)


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(sa.String, nullable=False)
    preco: Mapped[Decimal] = mapped_column(sa.Numeric(10, 2), nullable=False)
    categoria: Mapped[str] = mapped_column(sa.String, nullable=False)
    sazonal: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)
    ativo: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)

    estoques: Mapped[list["EstoqueUnidade"]] = relationship(back_populates="produto")

    def ativar(self) -> None:
        self.ativo = True

    def desativar(self) -> None:
        self.ativo = False


class EstoqueUnidade(Base):
    __tablename__ = "estoque_unidade"
    __table_args__ = (sa.UniqueConstraint("produto_id", "unidade_id", name="uq_estoque_produto_unidade"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False)
    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidades.id"), nullable=False)
    quantidade: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)

    produto: Mapped["Produto"] = relationship(back_populates="estoques")
    unidade: Mapped["Unidade"] = relationship(back_populates="estoques")

    def tem_saldo_suficiente(self, qtd: int) -> bool:
        return self.quantidade >= qtd

    def dar_entrada(self, qtd: int) -> None:
        self.quantidade += qtd

    def dar_baixa(self, qtd: int) -> None:
        if not self.tem_saldo_suficiente(qtd):
            raise EstoqueInsuficienteError(
                f"Saldo insuficiente: disponível {self.quantidade}, solicitado {qtd}."
            )
        self.quantidade -= qtd

    def zerado(self) -> bool:
        return self.quantidade == 0


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(sa.String, nullable=False)
    email: Mapped[str] = mapped_column(sa.String, unique=True, index=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(sa.String, nullable=False)
    role: Mapped[PerfilUsuario] = mapped_column(sa.Enum(PerfilUsuario), nullable=False)
    unidade_id: Mapped[Optional[int]] = mapped_column(ForeignKey("unidades.id"), nullable=True)
    cpf: Mapped[Optional[str]] = mapped_column(sa.String, unique=True, nullable=True)
    data_nascimento: Mapped[Optional[date]] = mapped_column(sa.Date, nullable=True)
    ativo: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)

    unidade: Mapped[Optional["Unidade"]] = relationship(back_populates="usuarios")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )
    consentimentos: Mapped[list["Consentimento"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )
    pedidos: Mapped[list["Pedido"]] = relationship(back_populates="cliente")

    def autenticar(self, senha: str) -> bool:
        from app.infrastructure.security.hashing import verificar_senha

        return self.ativo and verificar_senha(senha, self.senha_hash)

    def possui_permissao(self, roles_permitidos: list[PerfilUsuario]) -> bool:
        return self.ativo and self.role in roles_permitidos


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(sa.String, unique=True, nullable=False)
    expira_em: Mapped[datetime] = mapped_column(sa.DateTime, nullable=False)
    revogado: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)

    usuario: Mapped["Usuario"] = relationship(back_populates="refresh_tokens")

    def valido(self) -> bool:
        return not self.revogado and self.expira_em > datetime.utcnow()

    def revogar(self) -> None:
        self.revogado = True


class Consentimento(Base):
    __tablename__ = "consentimentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    tipo: Mapped[TipoConsentimento] = mapped_column(sa.Enum(TipoConsentimento), nullable=False)
    aceito: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)
    data_consentimento: Mapped[datetime] = mapped_column(sa.DateTime, nullable=False)

    usuario: Mapped["Usuario"] = relationship(back_populates="consentimentos")

    def revogar(self) -> None:
        self.aceito = False


class Pedido(Base):
    __tablename__ = "pedidos"

    _TRANSICOES_PERMITIDAS = {
        StatusPedido.PAGO: (StatusPedido.EM_PREPARO,),
        StatusPedido.EM_PREPARO: (StatusPedido.PRONTO,),
        StatusPedido.PRONTO: (StatusPedido.ENTREGUE,),
    }
    _STATUS_CANCELAVEIS = (
        StatusPedido.AGUARDANDO_PAGAMENTO,
        StatusPedido.PAGO,
        StatusPedido.EM_PREPARO,
        StatusPedido.PRONTO,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidades.id"), nullable=False)
    canal_pedido: Mapped[CanalPedido] = mapped_column(sa.Enum(CanalPedido), nullable=False)
    status: Mapped[StatusPedido] = mapped_column(
        sa.Enum(StatusPedido), default=StatusPedido.AGUARDANDO_PAGAMENTO, nullable=False
    )
    valor_total: Mapped[Decimal] = mapped_column(sa.Numeric(10, 2), default=0, nullable=False)
    desconto_fidelidade: Mapped[Decimal] = mapped_column(sa.Numeric(10, 2), default=0, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(sa.DateTime, default=datetime.utcnow, nullable=False)

    cliente: Mapped["Usuario"] = relationship(back_populates="pedidos")
    unidade: Mapped["Unidade"] = relationship()
    itens: Mapped[list["ItemPedido"]] = relationship(
        back_populates="pedido", cascade="all, delete-orphan"
    )

    def adicionar_item(self, item: "ItemPedido") -> None:
        self.itens.append(item)

    def calcular_total(self) -> Decimal:
        subtotal = sum((item.calcular_subtotal() for item in self.itens), Decimal("0"))
        return subtotal - (self.desconto_fidelidade or Decimal("0"))

    def aplicar_desconto_fidelidade(self, valor: Decimal) -> None:
        self.desconto_fidelidade = valor
        self.valor_total = self.calcular_total()

    def confirmar_pagamento(self) -> None:
        if self.status != StatusPedido.AGUARDANDO_PAGAMENTO:
            raise TransicaoStatusInvalidaError(
                f"Pedido no status {self.status.value} não está aguardando pagamento."
            )
        self.status = StatusPedido.PAGO

    def avancar_status(self, novo_status: StatusPedido) -> None:
        permitidos = self._TRANSICOES_PERMITIDAS.get(self.status, ())
        if novo_status not in permitidos:
            raise TransicaoStatusInvalidaError(
                f"Não é possível mudar de {self.status.value} para {novo_status.value}."
            )
        self.status = novo_status

    def pode_ser_cancelado(self) -> bool:
        return self.status in self._STATUS_CANCELAVEIS

    def cancelar(self) -> None:
        if not self.pode_ser_cancelado():
            raise PedidoNaoPodeSerCanceladoError(
                f"Pedido no status {self.status.value} não pode ser cancelado."
            )
        self.status = StatusPedido.CANCELADO


class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"), nullable=False)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False)
    quantidade: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    preco_unitario: Mapped[Decimal] = mapped_column(sa.Numeric(10, 2), nullable=False)

    pedido: Mapped["Pedido"] = relationship(back_populates="itens")
    produto: Mapped["Produto"] = relationship()

    def calcular_subtotal(self) -> Decimal:
        return self.preco_unitario * self.quantidade
