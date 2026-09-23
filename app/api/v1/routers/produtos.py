from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import exigir_perfis, get_current_usuario
from app.api.v1.schemas.produto_schemas import ProdutoCreate, ProdutoResponse, ProdutoUpdate
from app.domain.enums import PerfilUsuario
from app.infrastructure.db.models import Produto, Usuario
from app.infrastructure.db.repositories.produto_repository import ProdutoRepository
from app.infrastructure.db.session import get_db

router = APIRouter(prefix="/produtos", tags=["produtos"])


@router.get("", response_model=list[ProdutoResponse])
def listar_produtos(db: Session = Depends(get_db), _: Usuario = Depends(get_current_usuario)):
    return ProdutoRepository(db).listar()


@router.get("/{produto_id}", response_model=ProdutoResponse)
def obter_produto(
    produto_id: int, db: Session = Depends(get_db), _: Usuario = Depends(get_current_usuario)
):
    produto = ProdutoRepository(db).obter_por_id(produto_id)
    if produto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")
    return produto


@router.post("", response_model=ProdutoResponse, status_code=status.HTTP_201_CREATED)
def criar_produto(
    dados: ProdutoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(exigir_perfis(PerfilUsuario.ADMIN)),
):
    produto = Produto(
        nome=dados.nome, preco=dados.preco, categoria=dados.categoria, sazonal=dados.sazonal
    )
    return ProdutoRepository(db).criar(produto)


@router.put("/{produto_id}", response_model=ProdutoResponse)
def atualizar_produto(
    produto_id: int,
    dados: ProdutoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(exigir_perfis(PerfilUsuario.ADMIN)),
):
    repo = ProdutoRepository(db)
    produto = repo.obter_por_id(produto_id)
    if produto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(produto, campo, valor)

    return repo.atualizar(produto)


@router.delete("/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
def desativar_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(exigir_perfis(PerfilUsuario.ADMIN)),
):
    repo = ProdutoRepository(db)
    produto = repo.obter_por_id(produto_id)
    if produto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")

    produto.desativar()
    repo.atualizar(produto)


@router.post("/{produto_id}/ativar", response_model=ProdutoResponse)
def ativar_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(exigir_perfis(PerfilUsuario.ADMIN)),
):
    repo = ProdutoRepository(db)
    produto = repo.obter_por_id(produto_id)
    if produto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")

    produto.ativar()
    return repo.atualizar(produto)
