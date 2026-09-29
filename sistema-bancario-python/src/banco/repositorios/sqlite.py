"""Repositório SQLite (biblioteca padrão, sem dependências externas).

Valores monetários são gravados como TEXT para preservar o `Decimal` exato
(o tipo REAL do SQLite é ponto flutuante).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from decimal import Decimal

from ..dominio import Conta, TipoTransacao, Transacao

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS contas (
    numero  INTEGER PRIMARY KEY,
    titular TEXT NOT NULL,
    saldo   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS transacoes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    conta_numero  INTEGER NOT NULL REFERENCES contas(numero),
    tipo          TEXT NOT NULL,
    valor         TEXT NOT NULL,
    saldo_apos    TEXT NOT NULL,
    data_hora     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_transacoes_conta ON transacoes(conta_numero, id);
"""


class RepositorioSQLite:
    def __init__(self, caminho: str = ":memory:") -> None:
        # A conexão é compartilhada entre threads (API); o serviço serializa o acesso.
        self._conn = sqlite3.connect(caminho, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        with self._conn:
            self._conn.executescript(_ESQUEMA)

    def proximo_numero(self) -> int:
        linha = self._conn.execute("SELECT COALESCE(MAX(numero), 0) + 1 FROM contas")
        return int(linha.fetchone()[0])

    def adicionar(self, conta: Conta) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO contas (numero, titular, saldo) VALUES (?, ?, ?)",
                (conta.numero, conta.titular, str(conta.saldo)),
            )
            self._inserir_transacoes(conta.numero, conta.transacoes)

    def obter(self, numero: int) -> Conta | None:
        linha = self._conn.execute(
            "SELECT numero, titular, saldo FROM contas WHERE numero = ?", (numero,)
        ).fetchone()
        if linha is None:
            return None
        transacoes = [
            Transacao(
                tipo=TipoTransacao(t["tipo"]),
                valor=Decimal(t["valor"]),
                data_hora=datetime.fromisoformat(t["data_hora"]),
                saldo_apos=Decimal(t["saldo_apos"]),
            )
            for t in self._conn.execute(
                "SELECT tipo, valor, saldo_apos, data_hora FROM transacoes "
                "WHERE conta_numero = ? ORDER BY id",
                (numero,),
            )
        ]
        return Conta(linha["numero"], linha["titular"], Decimal(linha["saldo"]), transacoes)

    def salvar(self, conta: Conta) -> None:
        """Atualiza o saldo e grava só as transações novas, numa única transação SQL."""
        with self._conn:
            self._conn.execute(
                "UPDATE contas SET titular = ?, saldo = ? WHERE numero = ?",
                (conta.titular, str(conta.saldo), conta.numero),
            )
            ja_gravadas = self._conn.execute(
                "SELECT COUNT(*) FROM transacoes WHERE conta_numero = ?",
                (conta.numero,),
            ).fetchone()[0]
            self._inserir_transacoes(conta.numero, conta.transacoes[ja_gravadas:])

    def fechar(self) -> None:
        self._conn.close()

    def _inserir_transacoes(self, numero: int, transacoes: list[Transacao]) -> None:
        self._conn.executemany(
            "INSERT INTO transacoes (conta_numero, tipo, valor, saldo_apos, data_hora) "
            "VALUES (?, ?, ?, ?, ?)",
            [
                (numero, t.tipo.value, str(t.valor), str(t.saldo_apos), t.data_hora.isoformat())
                for t in transacoes
            ],
        )
