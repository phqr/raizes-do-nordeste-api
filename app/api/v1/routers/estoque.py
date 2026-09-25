from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import exigir_perfis, verificar_acesso_unidade
from app.api.v1.schemas.estoque_schemas import EntradaEstoqueRequest, EstoqueResponse
from app.domain.enums import PerfilUsuario
from app.infrastructure.db.models import Usuario
from app.infrastructure.db.repositories.estoque_repository import EstoqueRepository
from app.infrastructure.db.repositories.produto_repository import ProdutoRepository
from app.infrastructure.db.repositories.unidade_repository import UnidadeRepository
from app.infrastructure.db.session import get_db

router = APIRouter(prefix="/estoque", tags=["estoque"])


@router.post("/entrada", response_model=EstoqueResponse, status_code=status.HTTP_201_CREATED)
def registrar_entrada(
    dados: EntradaEstoqueRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(exigir_perfis(PerfilUsuario.GERENTE, PerfilUsuario.ADMIN)),
):
    verificar_acesso_unidade(usuario, dados.unidade_id)

    if UnidadeRepository(db).obter_por_id(dados.unidade_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")
    if ProdutoRepository(db).obter_por_id(dados.produto_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")

    repo = EstoqueRepository(db)
    estoque = repo.obter_ou_criar(dados.produto_id, dados.unidade_id)
    estoque.dar_entrada(dados.quantidade)
    return repo.salvar(estoque)


@router.get("", response_model=list[EstoqueResponse])
def consultar_saldo(
    unidade_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(exigir_perfis(PerfilUsuario.GERENTE, PerfilUsuario.ADMIN)),
):
    verificar_acesso_unidade(usuario, unidade_id)

    if UnidadeRepository(db).obter_por_id(unidade_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")

    return EstoqueRepository(db).listar_por_unidade(unidade_id)
