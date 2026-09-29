"""Utilitários para valores monetários.

Dinheiro é sempre `Decimal` com 2 casas decimais: `float` acumula erro de
arredondamento (0.1 + 0.2 != 0.3) e é inaceitável em sistemas financeiros.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Union

from .excecoes import ValorInvalidoError

CENTAVOS = Decimal("0.01")
ZERO = Decimal("0.00")

ValorEntrada = Union[Decimal, int, float, str]


def normalizar_valor(valor: ValorEntrada) -> Decimal:
    """Converte a entrada em `Decimal` positivo com 2 casas.

    Não arredonda em silêncio: 10.005 é rejeitado em vez de virar 10.00 ou 10.01.
    """
    if isinstance(valor, bool):
        raise ValorInvalidoError("Valor inválido.")
    try:
        decimal = Decimal(str(valor)) if isinstance(valor, float) else Decimal(valor)
        if not decimal.is_finite():
            raise ValorInvalidoError("Valor inválido.")
        if decimal <= 0:
            raise ValorInvalidoError("O valor deve ser maior que zero.")
        normalizado = decimal.quantize(CENTAVOS)
    except (InvalidOperation, TypeError, ValueError):
        raise ValorInvalidoError("Valor inválido.") from None
    if normalizado != decimal:
        raise ValorInvalidoError("O valor deve ter no máximo duas casas decimais.")
    return normalizado


def formatar_moeda(valor: Decimal) -> str:
    """Formata no padrão brasileiro: `R$ 1.234,56`."""
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "_").replace(".", ",").replace("_", ".")
