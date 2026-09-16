from datetime import date, datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import PerfilUsuario, TipoConsentimento
from app.infrastructure.db.session import Base


class Unidade(Base):
    __tablename__ = "unidades"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(sa.String, nullable=False)

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="unidade")


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
