"""Contrato de persistência.

O serviço depende apenas desta interface (inversão de dependência):
trocar SQLite por PostgreSQL ou Azure SQL é escrever uma nova implementação.
"""

from __future__ import annotations

from typing import Protocol

from ..dominio import Conta


class RepositorioContas(Protocol):
    def proximo_numero(self) -> int: ...

    def adicionar(self, conta: Conta) -> None: ...

    def obter(self, numero: int) -> Conta | None: ...

    def salvar(self, conta: Conta) -> None: ...
