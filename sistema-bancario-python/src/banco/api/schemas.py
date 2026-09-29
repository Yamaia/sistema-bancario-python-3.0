"""Contratos JSON da API (validação de entrada e formato de saída).

Valores monetários trafegam como string decimal ("100.00") na resposta,
evitando perda de precisão em clientes que usam float.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from ..dominio import TipoTransacao


class ContaCriar(BaseModel):
    titular: str = Field(min_length=2, max_length=120, examples=["Maria Silva"])


class OperacaoEntrada(BaseModel):
    valor: Decimal = Field(gt=0, max_digits=15, decimal_places=2, examples=["150.00"])


class ContaSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    numero: int
    titular: str
    saldo: Decimal


class TransacaoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tipo: TipoTransacao
    valor: Decimal
    data_hora: datetime
    saldo_apos: Decimal


class ExtratoSaida(ContaSaida):
    transacoes: list[TransacaoSaida]


class ErroSaida(BaseModel):
    codigo: str
    detalhe: str
