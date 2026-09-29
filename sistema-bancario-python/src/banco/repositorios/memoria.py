"""Repositório em memória — usado em testes e demonstrações."""

from __future__ import annotations

import copy

from ..dominio import Conta


class RepositorioMemoria:
    def __init__(self) -> None:
        self._contas: dict[int, Conta] = {}

    def proximo_numero(self) -> int:
        return max(self._contas, default=0) + 1

    def adicionar(self, conta: Conta) -> None:
        self._contas[conta.numero] = copy.deepcopy(conta)

    def obter(self, numero: int) -> Conta | None:
        conta = self._contas.get(numero)
        # Devolve cópia: só `salvar` altera o estado persistido, como num banco real.
        return copy.deepcopy(conta) if conta else None

    def salvar(self, conta: Conta) -> None:
        self._contas[conta.numero] = copy.deepcopy(conta)
