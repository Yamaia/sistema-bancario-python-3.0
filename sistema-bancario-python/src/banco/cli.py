"""Interface de linha de comando: `python -m banco.cli`."""

from __future__ import annotations

import argparse
from typing import Callable

from .apresentacao import formatar_extrato
from .dominio import ErroDominio, formatar_moeda
from .repositorios import RepositorioSQLite
from .servicos import ServicoBancario

MENU = """
[d] Depositar
[s] Sacar
[e] Extrato
[t] Trocar de conta
[q] Sair
=> """


def _ler_valor(entrada: Callable[[str], str]) -> str:
    """Aceita o formato brasileiro (1.234,56) e devolve texto para o serviço validar."""
    texto = entrada("Valor: ").strip()
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    return texto


def _escolher_conta(
    servico: ServicoBancario, entrada: Callable[[str], str], saida: Callable[[str], None]
) -> int | None:
    while True:
        texto = entrada("Número da conta ([n] nova conta, [q] sair): ").strip().lower()
        if texto == "q":
            return None
        try:
            if texto == "n":
                conta = servico.abrir_conta(entrada("Nome do titular: "))
                saida(f"Conta {conta.numero} criada com sucesso.")
            else:
                conta = servico.consultar_conta(int(texto))
            return conta.numero
        except ValueError:
            saida("Digite um número de conta válido.")
        except ErroDominio as erro:
            saida(f"Erro: {erro}")


def executar(
    servico: ServicoBancario,
    entrada: Callable[[str], str] = input,
    saida: Callable[[str], None] = print,
) -> None:
    saida(" SISTEMA BANCÁRIO ".center(44, "="))
    numero = _escolher_conta(servico, entrada, saida)
    while numero is not None:
        opcao = entrada(MENU).strip().lower()
        try:
            if opcao == "d":
                t = servico.depositar(numero, _ler_valor(entrada))
                saida(f"Depósito de {formatar_moeda(t.valor)} realizado.")
            elif opcao == "s":
                t = servico.sacar(numero, _ler_valor(entrada))
                saida(f"Saque de {formatar_moeda(t.valor)} realizado.")
            elif opcao == "e":
                saida(formatar_extrato(servico.extrato(numero)))
            elif opcao == "t":
                numero = _escolher_conta(servico, entrada, saida)
            elif opcao == "q":
                break
            else:
                saida("Opção inválida, tente novamente.")
        except ErroDominio as erro:
            saida(f"Operação não realizada: {erro}")
    saida("Até logo!")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Sistema bancário (CLI)")
    parser.add_argument("--db", default="banco.db", help="arquivo SQLite (padrão: banco.db)")
    args = parser.parse_args(argv)
    repositorio = RepositorioSQLite(args.db)
    try:
        executar(ServicoBancario(repositorio))
    except (EOFError, KeyboardInterrupt):
        print("\nAté logo!")
    finally:
        repositorio.fechar()


if __name__ == "__main__":
    main()
