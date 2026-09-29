"""API REST (FastAPI).

Rodar:  uvicorn banco.api.app:criar_app --factory --reload
Docs:   http://127.0.0.1:8000/docs
"""

from __future__ import annotations

import os
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from .. import __version__
from ..dominio import (
    ContaNaoEncontradaError,
    ErroDominio,
    TipoTransacao,
)
from ..repositorios import RepositorioSQLite
from ..servicos import ServicoBancario
from .schemas import (
    ContaCriar,
    ContaSaida,
    ErroSaida,
    ExtratoSaida,
    OperacaoEntrada,
    TransacaoSaida,
)


def obter_servico(request: Request) -> ServicoBancario:
    return request.app.state.servico


ServicoDep = Annotated[ServicoBancario, Depends(obter_servico)]

_ERROS = {404: {"model": ErroSaida, "description": "Conta não encontrada"},
          422: {"model": ErroSaida, "description": "Regra de negócio violada"}}

router = APIRouter(prefix="/contas", tags=["Contas"])


@router.post("", response_model=ContaSaida, status_code=201, summary="Abrir conta")
def abrir_conta(dados: ContaCriar, servico: ServicoDep):
    return servico.abrir_conta(dados.titular)


@router.get("/{numero}", response_model=ContaSaida, responses=_ERROS, summary="Consultar conta")
def consultar_conta(numero: int, servico: ServicoDep):
    return servico.consultar_conta(numero)


@router.post(
    "/{numero}/depositos",
    response_model=TransacaoSaida,
    status_code=201,
    responses=_ERROS,
    summary="Depositar",
)
def depositar(numero: int, dados: OperacaoEntrada, servico: ServicoDep):
    return servico.depositar(numero, dados.valor)


@router.post(
    "/{numero}/saques",
    response_model=TransacaoSaida,
    status_code=201,
    responses=_ERROS,
    summary="Sacar",
)
def sacar(numero: int, dados: OperacaoEntrada, servico: ServicoDep):
    return servico.sacar(numero, dados.valor)


@router.get("/{numero}/extrato", response_model=ExtratoSaida, responses=_ERROS, summary="Extrato")
def extrato(numero: int, servico: ServicoDep, tipo: TipoTransacao | None = None):
    return servico.extrato(numero, tipo)


def criar_app(servico: ServicoBancario | None = None) -> FastAPI:
    """Fábrica da aplicação. Sem `servico`, usa SQLite em `$BANCO_DB` (padrão: banco.db)."""
    if servico is None:
        servico = ServicoBancario(RepositorioSQLite(os.getenv("BANCO_DB", "banco.db")))

    app = FastAPI(
        title="Sistema Bancário",
        description="Depósito, saque e extrato com regras de negócio configuráveis.",
        version=__version__,
    )
    app.state.servico = servico
    app.include_router(router)

    @app.exception_handler(ErroDominio)
    async def tratar_erro_dominio(_: Request, erro: ErroDominio) -> JSONResponse:
        status = 404 if isinstance(erro, ContaNaoEncontradaError) else 422
        return JSONResponse(
            status_code=status,
            content={"codigo": type(erro).__name__, "detalhe": str(erro)},
        )

    @app.get("/saude", tags=["Infra"], summary="Health check")
    def saude() -> dict[str, str]:
        return {"status": "ok"}

    return app
