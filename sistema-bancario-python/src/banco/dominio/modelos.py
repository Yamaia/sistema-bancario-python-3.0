"""Entidades do domínio: transações, política da conta e a própria conta."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from .dinheiro import ZERO, ValorEntrada, formatar_moeda, normalizar_valor
from .excecoes import (
    LimiteSaqueExcedidoError,
    LimiteSaquesDiariosExcedidoError,
    SaldoInsuficienteError,
)


class TipoTransacao(str, Enum):
    DEPOSITO = "deposito"
    SAQUE = "saque"
    TARIFA = "tarifa"


@dataclass(frozen=True, slots=True)
class Transacao:
    """Movimentação imutável registrada no extrato."""

    tipo: TipoTransacao
    valor: Decimal
    data_hora: datetime
    saldo_apos: Decimal


@dataclass(frozen=True, slots=True)
class PoliticaConta:
    """Regras comerciais do banco, configuráveis sem mexer no código da conta.

    `tarifa_saque` é o ponto de monetização: valor cobrado a cada saque
    (padrão 0, como no enunciado do desafio).
    """

    limite_por_saque: Decimal = Decimal("500.00")
    limite_saques_diarios: int = 3
    tarifa_saque: Decimal = ZERO

    def __post_init__(self) -> None:
        if self.limite_por_saque <= 0:
            raise ValueError("limite_por_saque deve ser positivo.")
        if self.limite_saques_diarios < 0:
            raise ValueError("limite_saques_diarios não pode ser negativo.")
        if self.tarifa_saque < 0:
            raise ValueError("tarifa_saque não pode ser negativa.")


@dataclass(frozen=True, slots=True)
class Extrato:
    """Visão de leitura de uma conta: saldo atual e movimentações."""

    numero: int
    titular: str
    saldo: Decimal
    transacoes: tuple[Transacao, ...]


@dataclass
class Conta:
    """Conta bancária. Concentra as regras de depósito e saque."""

    numero: int
    titular: str
    saldo: Decimal = ZERO
    transacoes: list[Transacao] = field(default_factory=list)

    def depositar(self, valor: ValorEntrada, agora: datetime) -> Transacao:
        valor = normalizar_valor(valor)
        self.saldo += valor
        return self._registrar(TipoTransacao.DEPOSITO, valor, agora)

    def sacar(
        self, valor: ValorEntrada, agora: datetime, politica: PoliticaConta
    ) -> Transacao:
        """Aplica todas as validações *antes* de alterar qualquer estado."""
        valor = normalizar_valor(valor)

        if valor > politica.limite_por_saque:
            raise LimiteSaqueExcedidoError(
                f"O limite por saque é {formatar_moeda(politica.limite_por_saque)}."
            )
        if self.saques_no_dia(agora.date()) >= politica.limite_saques_diarios:
            raise LimiteSaquesDiariosExcedidoError(
                f"Limite de {politica.limite_saques_diarios} saques diários atingido."
            )
        if valor + politica.tarifa_saque > self.saldo:
            raise SaldoInsuficienteError(
                f"Saldo insuficiente. Saldo atual: {formatar_moeda(self.saldo)}."
            )

        self.saldo -= valor
        saque = self._registrar(TipoTransacao.SAQUE, valor, agora)
        if politica.tarifa_saque > 0:
            self.saldo -= politica.tarifa_saque
            self._registrar(TipoTransacao.TARIFA, politica.tarifa_saque, agora)
        return saque

    def saques_no_dia(self, dia: date) -> int:
        return sum(
            1
            for t in self.transacoes
            if t.tipo is TipoTransacao.SAQUE and t.data_hora.date() == dia
        )

    def extrato(self, tipo: TipoTransacao | None = None) -> Extrato:
        transacoes = tuple(
            t for t in self.transacoes if tipo is None or t.tipo is tipo
        )
        return Extrato(self.numero, self.titular, self.saldo, transacoes)

    def _registrar(
        self, tipo: TipoTransacao, valor: Decimal, agora: datetime
    ) -> Transacao:
        transacao = Transacao(tipo, valor, agora, self.saldo)
        self.transacoes.append(transacao)
        return transacao
