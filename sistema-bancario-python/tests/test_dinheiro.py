from decimal import Decimal

import pytest

from banco.dominio import ValorInvalidoError, formatar_moeda, normalizar_valor


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        (100, "100.00"),
        ("100", "100.00"),
        ("10.5", "10.50"),
        (10.5, "10.50"),
        (0.1, "0.10"),
        (Decimal("0.01"), "0.01"),
        (" 25.00 ", "25.00"),
    ],
)
def test_normaliza_valores_validos(entrada, esperado):
    assert normalizar_valor(entrada) == Decimal(esperado)


@pytest.mark.parametrize(
    "entrada",
    [0, -1, "-5", "abc", "", None, True, "NaN", "Infinity", "10.005", 1e50, "1e50", [], {}],
)
def test_rejeita_valores_invalidos(entrada):
    with pytest.raises(ValorInvalidoError):
        normalizar_valor(entrada)


def test_nao_arredonda_em_silencio():
    with pytest.raises(ValorInvalidoError, match="duas casas"):
        normalizar_valor("10.005")


@pytest.mark.parametrize(
    "valor, esperado",
    [
        ("0.00", "R$ 0,00"),
        ("5", "R$ 5,00"),
        ("1234.5", "R$ 1.234,50"),
        ("1234567.89", "R$ 1.234.567,89"),
    ],
)
def test_formatar_moeda(valor, esperado):
    assert formatar_moeda(Decimal(valor)) == esperado
