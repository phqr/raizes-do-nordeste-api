"""
Popula o banco com o mínimo para usar e demonstrar a API:

- o primeiro usuário ADMIN (necessário porque /auth/registrar-interno exige GERENTE/ADMIN logado);
- dados de demonstração para executar o Fluxo A no Postman: uma unidade, produtos com estoque, um CLIENTE e um usuário da COZINHA.

Uso (a partir da raiz do projeto, após `alembic upgrade head`):
    python -m scripts.seed
"""

from datetime import datetime
from decimal import Decimal

from app.domain.enums import PerfilUsuario, TipoConsentimento, TipoOperacaoUnidade
from app.infrastructure.db.models import (
    Consentimento,
    EstoqueUnidade,
    Produto,
    Unidade,
    Usuario,
)
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.security.hashing import hash_senha

# Senha de todos os usuários do seed, inclusive o ADMIN (só para testes locais).
SENHA_DEMO = "Demo@1234"
ADMIN_EMAIL = "admin@raizesdonordeste.com"

UNIDADE = {"nome": "Raízes do Nordeste - Recife Centro", "endereco": "Rua da Aurora, 100 - Recife/PE"}

# (nome, preço, categoria, quantidade em estoque na unidade)
PRODUTOS = [
    ("Tapioca de carne de sol", Decimal("18.90"), "Tapiocas", 50),
    ("Cuscuz com queijo coalho", Decimal("14.50"), "Cuscuz", 50),
    ("Suco de cajá", Decimal("8.00"), "Bebidas", 100),
]


def _obter_ou_criar_usuario(db, email: str, **campos) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is None:
        usuario = Usuario(email=email, **campos)
        db.add(usuario)
        db.flush()
        print(f"Usuário {campos['role'].value} '{email}' criado.")
    return usuario


if __name__ == "__main__":
    db = SessionLocal()
    try:
        _obter_ou_criar_usuario(
            db,
            ADMIN_EMAIL,
            nome="Administrador",
            senha_hash=hash_senha(SENHA_DEMO),
            role=PerfilUsuario.ADMIN,
        )

        unidade = db.query(Unidade).filter(Unidade.nome == UNIDADE["nome"]).first()
        if unidade is None:
            unidade = Unidade(**UNIDADE, tipo_operacao=TipoOperacaoUnidade.COMPLETA)
            db.add(unidade)
            db.flush()
            print(f"Unidade '{unidade.nome}' criada.")

        for nome, preco, categoria, quantidade in PRODUTOS:
            produto = db.query(Produto).filter(Produto.nome == nome).first()
            if produto is None:
                produto = Produto(nome=nome, preco=preco, categoria=categoria)
                db.add(produto)
                db.flush()
                print(f"Produto '{nome}' criado.")

            estoque = (
                db.query(EstoqueUnidade)
                .filter(EstoqueUnidade.produto_id == produto.id, EstoqueUnidade.unidade_id == unidade.id)
                .first()
            )
            if estoque is None:
                db.add(EstoqueUnidade(produto_id=produto.id, unidade_id=unidade.id, quantidade=quantidade))

        cliente = _obter_ou_criar_usuario(
            db,
            "cliente@raizesdonordeste.com",
            nome="Cliente Demonstração",
            senha_hash=hash_senha(SENHA_DEMO),
            role=PerfilUsuario.CLIENTE,
            cpf="52998224725",
        )
        # Consentimentos LGPD (cadastro) e do programa de fidelidade, para o pedido entregue gerar pontos.
        if not cliente.consentimentos:
            for tipo in (TipoConsentimento.CADASTRO_LGPD, TipoConsentimento.FIDELIDADE):
                cliente.consentimentos.append(
                    Consentimento(tipo=tipo, aceito=True, data_consentimento=datetime.now())
                )

        _obter_ou_criar_usuario(
            db,
            "cozinha@raizesdonordeste.com",
            nome="Cozinha Recife Centro",
            senha_hash=hash_senha(SENHA_DEMO),
            role=PerfilUsuario.COZINHA,
            unidade_id=unidade.id,
        )

        db.commit()
    finally:
        db.close()
