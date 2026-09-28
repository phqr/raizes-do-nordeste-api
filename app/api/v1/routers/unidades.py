from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import exigir_perfis, get_current_usuario
from app.api.v1.schemas.unidade_schemas import (
    ItemCardapioResponse,
    UnidadeCreate,
    UnidadeResponse,
    UnidadeUpdate,
)
from app.domain.enums import PerfilUsuario
from app.infrastructure.db.models import Unidade, Usuario
from app.infrastructure.db.repositories.estoque_repository import EstoqueRepository
from app.infrastructure.db.repositories.unidade_repository import UnidadeRepository
from app.infrastructure.db.session import get_db

router = APIRouter(prefix="/unidades", tags=["unidades"])


@router.get("", response_model=list[UnidadeResponse])
def listar_unidades(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_usuario),
):
    return UnidadeRepository(db).listar(page=page, limit=limit)


@router.get("/{unidade_id}", response_model=UnidadeResponse)
def obter_unidade(
    unidade_id: int, db: Session = Depends(get_db), _: Usuario = Depends(get_current_usuario)
):
    unidade = UnidadeRepository(db).obter_por_id(unidade_id)
    if unidade is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")
    return unidade


@router.get("/{unidade_id}/cardapio", response_model=list[ItemCardapioResponse])
def consultar_cardapio(unidade_id: int, db: Session = Depends(get_db), _: Usuario = Depends(get_current_usuario)):
    if UnidadeRepository(db).obter_por_id(unidade_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")

    return EstoqueRepository(db).listar_cardapio_unidade(unidade_id)


@router.post("", response_model=UnidadeResponse, status_code=status.HTTP_201_CREATED)
def criar_unidade(
    dados: UnidadeCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(exigir_perfis(PerfilUsuario.ADMIN)),
):
    unidade = Unidade(nome=dados.nome, endereco=dados.endereco, tipo_operacao=dados.tipo_operacao)
    return UnidadeRepository(db).criar(unidade)


@router.put("/{unidade_id}", response_model=UnidadeResponse)
def atualizar_unidade(
    unidade_id: int,
    dados: UnidadeUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(exigir_perfis(PerfilUsuario.ADMIN)),
):
    repo = UnidadeRepository(db)
    unidade = repo.obter_por_id(unidade_id)
    if unidade is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")

    for campo, valor in dados.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(unidade, campo, valor)

    return repo.atualizar(unidade)


@router.delete("/{unidade_id}", status_code=status.HTTP_204_NO_CONTENT)
def desativar_unidade(
    unidade_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(exigir_perfis(PerfilUsuario.ADMIN)),
):
    repo = UnidadeRepository(db)
    unidade = repo.obter_por_id(unidade_id)
    if unidade is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")

    unidade.ativo = False
    repo.atualizar(unidade)
