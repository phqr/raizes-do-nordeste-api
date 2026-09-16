"""
Cria o primeiro usuário ADMIN, direto no banco, sem passar pela API.

Uso (a partir da raiz do projeto, após `alembic upgrade head`):
    python -m scripts.seed_admin

Requer ADMIN_EMAIL e ADMIN_SENHA definidos no .env.
"""

import sys

from app.core.config import settings
from app.domain.enums import PerfilUsuario
from app.infrastructure.db.models import Usuario
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.security.hashing import hash_senha


def seed_admin() -> None:
    if not settings.admin_email or not settings.admin_senha:
        print("Defina ADMIN_EMAIL e ADMIN_SENHA no .env antes de rodar o seed.")
        sys.exit(1)

    db = SessionLocal()
    try:
        if db.query(Usuario).filter(Usuario.email == settings.admin_email).first():
            print(f"Usuário '{settings.admin_email}' já existe.")
            return

        admin = Usuario(
            nome="Administrador",
            email=settings.admin_email,
            senha_hash=hash_senha(settings.admin_senha),
            role=PerfilUsuario.ADMIN,
        )
        db.add(admin)
        db.commit()
        print(f"Usuário ADMIN '{settings.admin_email}' criado com sucesso.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
