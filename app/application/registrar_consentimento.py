from sqlalchemy.orm import Session

from app.domain.enums import TipoConsentimento
from app.infrastructure.db.models import Consentimento
from app.infrastructure.db.repositories.usuario_repository import ConsentimentoRepository


def registrar_consentimento(
    db: Session, usuario_id: int, tipo: TipoConsentimento, aceito: bool
) -> Consentimento:
    return ConsentimentoRepository(db).registrar(usuario_id=usuario_id, tipo=tipo, aceito=aceito)
