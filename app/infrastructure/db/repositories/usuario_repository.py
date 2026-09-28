from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.enums import TipoConsentimento
from app.infrastructure.db.models import Consentimento, RefreshToken, Usuario


class UsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def obter_por_id(self, usuario_id: int) -> Optional[Usuario]:
        return self.db.get(Usuario, usuario_id)

    def obter_por_email(self, email: str) -> Optional[Usuario]:
        return self.db.query(Usuario).filter(Usuario.email == email).first()

    def obter_por_cpf(self, cpf: str) -> Optional[Usuario]:
        return self.db.query(Usuario).filter(Usuario.cpf == cpf).first()

    def criar(self, usuario: Usuario) -> Usuario:
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def criar(self, usuario_id: int, token_hash: str, expira_em: datetime) -> RefreshToken:
        refresh_token = RefreshToken(usuario_id=usuario_id, token_hash=token_hash, expira_em=expira_em)
        self.db.add(refresh_token)
        self.db.commit()
        self.db.refresh(refresh_token)
        return refresh_token

    def obter_por_hash(self, token_hash: str) -> Optional[RefreshToken]:
        return self.db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    def revogar(self, refresh_token: RefreshToken) -> None:
        refresh_token.revogar()
        self.db.commit()


class ConsentimentoRepository:
    def __init__(self, db: Session):
        self.db = db

    def registrar(self, usuario_id: int, tipo: TipoConsentimento, aceito: bool) -> Consentimento:
        consentimento = Consentimento(
            usuario_id=usuario_id,
            tipo=tipo,
            aceito=aceito,
            data_consentimento=datetime.utcnow(),
        )
        self.db.add(consentimento)
        self.db.commit()
        self.db.refresh(consentimento)
        return consentimento
