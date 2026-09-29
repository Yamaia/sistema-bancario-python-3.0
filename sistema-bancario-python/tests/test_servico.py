import threading
from decimal import Decimal

import pytest

from banco.dominio import (
    ContaNaoEncontradaError,
    LimiteSaquesDiariosExcedidoError,
    PoliticaConta,
    SaldoInsuficienteError,
    TipoTransacao,
    TitularInvalidoError,
)
from banco.repositorios import RepositorioSQLite
from banco.servicos import ServicoBancario


def test_abrir_conta_gera_numeros_sequenciais(servico):
    assert servico.abrir_conta("Maria Silva").numero == 1
    assert servico.abrir_conta("João Souza").numero == 2


def test_titular_e_normalizado(servico):
    assert servico.abrir_conta("  Maria    Silva ").titular == "Maria Silva"


@pytest.mark.parametrize("titular", ["", " ", "A", "x" * 121, None])
def test_titular_invalido(servico, titular):
    with pytest.raises(TitularInvalidoError):
        servico.abrir_conta(titular)


def test_conta_inexistente(servico):
    for operacao in (
        lambda: servico.consultar_conta(99),
        lambda: servico.depositar(99, 10),
        lambda: servico.sacar(99, 10),
        lambda: servico.extrato(99),
    ):
        with pytest.raises(ContaNaoEncontradaError):
            operacao()


def test_fluxo_completo(servico, relogio):
    conta = servico.abrir_conta("Maria")
    servico.depositar(conta.numero, "1000.00")
    relogio.avancar(minutes=5)
    servico.sacar(conta.numero, "250.75")

    extrato = servico.extrato(conta.numero)
    assert extrato.saldo == Decimal("749.25")
    assert [(t.tipo, t.valor) for t in extrato.transacoes] == [
        (TipoTransacao.DEPOSITO, Decimal("1000.00")),
        (TipoTransacao.SAQUE, Decimal("250.75")),
    ]
    assert extrato.transacoes[1].data_hora > extrato.transacoes[0].data_hora


def test_operacao_com_erro_nao_persiste_nada(servico):
    conta = servico.abrir_conta("Maria")
    servico.depositar(conta.numero, 50)
    with pytest.raises(SaldoInsuficienteError):
        servico.sacar(conta.numero, 60)
    extrato = servico.extrato(conta.numero)
    assert extrato.saldo == Decimal("50.00") and len(extrato.transacoes) == 1


def test_limite_diario_respeita_o_relogio(servico, relogio):
    conta = servico.abrir_conta("Maria")
    servico.depositar(conta.numero, 500)
    for _ in range(3):
        servico.sacar(conta.numero, 10)
    with pytest.raises(LimiteSaquesDiariosExcedidoError):
        servico.sacar(conta.numero, 10)
    relogio.avancar(days=1)
    servico.sacar(conta.numero, 10)


def test_saldo_devolvido_e_copia(servico):
    conta = servico.abrir_conta("Maria")
    servico.consultar_conta(conta.numero).saldo = Decimal("999999")
    assert servico.consultar_conta(conta.numero).saldo == Decimal("0.00")


def test_dados_persistem_em_arquivo_sqlite(tmp_path, relogio):
    caminho = str(tmp_path / "banco.db")
    repo = RepositorioSQLite(caminho)
    s1 = ServicoBancario(repo, relogio=relogio)
    conta = s1.abrir_conta("Maria")
    s1.depositar(conta.numero, "123.45")
    s1.sacar(conta.numero, "23.45")
    repo.fechar()

    repo2 = RepositorioSQLite(caminho)
    extrato = ServicoBancario(repo2, relogio=relogio).extrato(conta.numero)
    repo2.fechar()
    assert extrato.saldo == Decimal("100.00")
    assert [t.tipo for t in extrato.transacoes] == [TipoTransacao.DEPOSITO, TipoTransacao.SAQUE]
    assert extrato.transacoes[0].data_hora == relogio.agora


def test_depositos_concorrentes_nao_perdem_valor(servico):
    conta = servico.abrir_conta("Maria")
    threads = [
        threading.Thread(target=servico.depositar, args=(conta.numero, "1.00"))
        for _ in range(50)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    extrato = servico.extrato(conta.numero)
    assert extrato.saldo == Decimal("50.00") and len(extrato.transacoes) == 50


def test_saques_concorrentes_respeitam_limite_diario(repositorio, relogio):
    servico = ServicoBancario(repositorio, PoliticaConta(limite_saques_diarios=3), relogio)
    conta = servico.abrir_conta("Maria")
    servico.depositar(conta.numero, 1000)
    resultados: list[bool] = []

    def tentar():
        try:
            servico.sacar(conta.numero, 10)
            resultados.append(True)
        except LimiteSaquesDiariosExcedidoError:
            resultados.append(False)

    threads = [threading.Thread(target=tentar) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert resultados.count(True) == 3
    assert servico.consultar_conta(conta.numero).saldo == Decimal("970.00")
