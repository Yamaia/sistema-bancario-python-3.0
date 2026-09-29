from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from banco.dominio import (
    Conta,
    LimiteSaqueExcedidoError,
    LimiteSaquesDiariosExcedidoError,
    PoliticaConta,
    SaldoInsuficienteError,
    TipoTransacao,
    ValorInvalidoError,
)

AGORA = datetime(2026, 3, 15, 10, 0)
POLITICA = PoliticaConta()


@pytest.fixture
def conta() -> Conta:
    return Conta(numero=1, titular="Maria")


def test_deposito_aumenta_saldo_e_registra(conta):
    t = conta.depositar("150.50", AGORA)
    assert conta.saldo == Decimal("150.50")
    assert (t.tipo, t.valor, t.saldo_apos) == (
        TipoTransacao.DEPOSITO,
        Decimal("150.50"),
        Decimal("150.50"),
    )
    assert conta.transacoes == [t]


@pytest.mark.parametrize("valor", [0, -10, "abc"])
def test_deposito_invalido_nao_altera_estado(conta, valor):
    with pytest.raises(ValorInvalidoError):
        conta.depositar(valor, AGORA)
    assert conta.saldo == Decimal("0.00") and conta.transacoes == []


def test_saque_diminui_saldo(conta):
    conta.depositar(300, AGORA)
    conta.sacar(120, AGORA, POLITICA)
    assert conta.saldo == Decimal("180.00")
    assert [t.tipo for t in conta.transacoes] == [TipoTransacao.DEPOSITO, TipoTransacao.SAQUE]


def test_saque_maior_que_saldo(conta):
    conta.depositar(100, AGORA)
    with pytest.raises(SaldoInsuficienteError):
        conta.sacar(100.01, AGORA, POLITICA)
    assert conta.saldo == Decimal("100.00") and len(conta.transacoes) == 1


def test_saque_pode_zerar_a_conta(conta):
    conta.depositar(100, AGORA)
    conta.sacar(100, AGORA, POLITICA)
    assert conta.saldo == Decimal("0.00")


def test_limite_por_saque(conta):
    conta.depositar(2000, AGORA)
    conta.sacar(500, AGORA, POLITICA)  # exatamente no limite: permitido
    with pytest.raises(LimiteSaqueExcedidoError):
        conta.sacar("500.01", AGORA, POLITICA)


def test_limite_de_saques_diarios(conta):
    conta.depositar(1000, AGORA)
    for _ in range(3):
        conta.sacar(10, AGORA, POLITICA)
    with pytest.raises(LimiteSaquesDiariosExcedidoError):
        conta.sacar(10, AGORA, POLITICA)
    assert conta.saldo == Decimal("970.00")


def test_limite_diario_zera_no_dia_seguinte(conta):
    conta.depositar(1000, AGORA)
    for _ in range(3):
        conta.sacar(10, AGORA, POLITICA)
    conta.sacar(10, AGORA + timedelta(days=1), POLITICA)
    assert conta.saldo == Decimal("960.00")


def test_deposito_nao_conta_no_limite_de_saques(conta):
    for _ in range(5):
        conta.depositar(10, AGORA)
    conta.sacar(10, AGORA, POLITICA)
    assert conta.saques_no_dia(AGORA.date()) == 1


def test_tarifa_de_saque_e_cobrada_e_registrada(conta):
    politica = PoliticaConta(tarifa_saque=Decimal("2.50"))
    conta.depositar(100, AGORA)
    conta.sacar(50, AGORA, politica)
    assert conta.saldo == Decimal("47.50")
    assert [t.tipo for t in conta.transacoes] == [
        TipoTransacao.DEPOSITO,
        TipoTransacao.SAQUE,
        TipoTransacao.TARIFA,
    ]


def test_tarifa_entra_na_checagem_de_saldo(conta):
    politica = PoliticaConta(tarifa_saque=Decimal("2.00"))
    conta.depositar(100, AGORA)
    with pytest.raises(SaldoInsuficienteError):
        conta.sacar(100, AGORA, politica)  # 100 + 2 > 100
    assert conta.saldo == Decimal("100.00")


def test_precisao_decimal(conta):
    for _ in range(10):
        conta.depositar("0.10", AGORA)
    assert conta.saldo == Decimal("1.00")  # com float daria 0.9999999999999999


def test_extrato_filtra_por_tipo(conta):
    conta.depositar(100, AGORA)
    conta.sacar(10, AGORA, POLITICA)
    assert len(conta.extrato().transacoes) == 2
    apenas_saques = conta.extrato(TipoTransacao.SAQUE).transacoes
    assert [t.tipo for t in apenas_saques] == [TipoTransacao.SAQUE]


@pytest.mark.parametrize(
    "kwargs",
    [{"limite_por_saque": Decimal("0")}, {"limite_saques_diarios": -1}, {"tarifa_saque": Decimal("-1")}],
)
def test_politica_valida_parametros(kwargs):
    with pytest.raises(ValueError):
        PoliticaConta(**kwargs)
