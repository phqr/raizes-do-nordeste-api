from datetime import date, datetime
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import PerfilUsuario, TipoConsentimento, TipoOperacaoUnidade
from app.domain.exceptions import EstoqueInsuficienteError
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
