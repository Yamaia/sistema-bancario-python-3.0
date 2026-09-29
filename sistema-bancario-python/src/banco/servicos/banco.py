"""Casos de uso do banco: abrir conta, depositar, sacar e consultar extrato."""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Callable

from ..dominio import (
    Conta,
    ContaNaoEncontradaError,
    Extrato,
    PoliticaConta,
    TipoTransacao,
    TitularInvalidoError,
    Transacao,
)
from ..dominio.dinheiro import ValorEntrada
from ..repositorios import RepositorioContas

_TAMANHO_MIN_TITULAR = 2
_TAMANHO_MAX_TITULAR = 120


class ServicoBancario:
    """Orquestra domínio + persistência.

    - `relogio` é injetável: os testes controlam "que horas são" sem mocks.
    - Um lock serializa o ciclo ler → alterar → salvar, evitando que dois
      saques simultâneos furem o limite ou o saldo (condição de corrida).
    """

    def __init__(
        self,
        repositorio: RepositorioContas,
        politica: PoliticaConta | None = None,
        relogio: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._repositorio = repositorio
        self._politica = politica or PoliticaConta()
        self._relogio = relogio
        self._lock = threading.RLock()

    @property
    def politica(self) -> PoliticaConta:
        return self._politica

    def abrir_conta(self, titular: str) -> Conta:
        nome = " ".join(titular.split()) if isinstance(titular, str) else ""
        if not _TAMANHO_MIN_TITULAR <= len(nome) <= _TAMANHO_MAX_TITULAR:
            raise TitularInvalidoError(
                f"O nome do titular deve ter entre {_TAMANHO_MIN_TITULAR} "
                f"e {_TAMANHO_MAX_TITULAR} caracteres."
            )
        with self._lock:
            conta = Conta(numero=self._repositorio.proximo_numero(), titular=nome)
            self._repositorio.adicionar(conta)
            return conta

    def consultar_conta(self, numero: int) -> Conta:
        with self._lock:
            return self._obter(numero)

    def depositar(self, numero: int, valor: ValorEntrada) -> Transacao:
        with self._lock:
            conta = self._obter(numero)
            transacao = conta.depositar(valor, self._relogio())
            self._repositorio.salvar(conta)
            return transacao

    def sacar(self, numero: int, valor: ValorEntrada) -> Transacao:
        with self._lock:
            conta = self._obter(numero)
            transacao = conta.sacar(valor, self._relogio(), self._politica)
            self._repositorio.salvar(conta)
            return transacao

    def extrato(self, numero: int, tipo: TipoTransacao | None = None) -> Extrato:
        with self._lock:
            return self._obter(numero).extrato(tipo)

    def _obter(self, numero: int) -> Conta:
        conta = self._repositorio.obter(numero)
        if conta is None:
            raise ContaNaoEncontradaError(f"Conta {numero} não encontrada.")
        return conta
