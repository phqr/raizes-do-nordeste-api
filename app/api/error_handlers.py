from collections.abc import Mapping
from http import HTTPStatus
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

_CODIGOS = {
    400: "REQUISICAO_INVALIDA",
    401: "NAO_AUTENTICADO",
    403: "SEM_PERMISSAO",
    404: "NAO_ENCONTRADO",
    405: "METODO_NAO_PERMITIDO",
    409: "CONFLITO",
    422: "VALIDACAO",
    500: "ERRO_INTERNO",
}

# Usadas quando o erro vem do próprio framework, com a frase padrão em inglês (ex.: rota inexistente).
_MENSAGENS_PADRAO = {
    404: "Recurso não encontrado.",
    405: "Método não permitido para este recurso.",
}


def _resposta_erro(
    status: int,
    mensagem: str,
    detalhes: Optional[list[dict]] = None,
    headers: Optional[Mapping[str, str]] = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "status": status,
            "codigo": _CODIGOS.get(status, "ERRO"),
            "mensagem": mensagem,
            "detalhes": detalhes or [],
        },
        headers=headers,
    )


def registrar_tratamento_de_erros(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def erro_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        mensagem = str(exc.detail)
        if mensagem == HTTPStatus(exc.status_code).phrase:
            mensagem = _MENSAGENS_PADRAO.get(exc.status_code, mensagem)
        return _resposta_erro(exc.status_code, mensagem, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def erro_validacao(request: Request, exc: RequestValidationError) -> JSONResponse:
        # O primeiro item de `loc` diz onde está o campo (body, query, path), o resto é o caminho dele.
        detalhes = [
            {
                "campo": ".".join(str(parte) for parte in erro["loc"][1:]) or str(erro["loc"][0]),
                "mensagem": erro["msg"],
            }
            for erro in exc.errors()
        ]
        return _resposta_erro(422, "Dados inválidos na requisição.", detalhes)

    @app.exception_handler(Exception)
    async def erro_inesperado(request: Request, exc: Exception) -> JSONResponse:
        return _resposta_erro(500, "Erro interno do servidor.")
