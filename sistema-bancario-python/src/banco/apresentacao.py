"""Formatação de texto para a CLI (a API devolve JSON, sem formatação)."""

from __future__ import annotations

from .dominio import Extrato, TipoTransacao, formatar_moeda

_ROTULOS = {
    TipoTransacao.DEPOSITO: "Depósito",
    TipoTransacao.SAQUE: "Saque",
    TipoTransacao.TARIFA: "Tarifa",
}
_LARGURA = 44


def formatar_extrato(extrato: Extrato) -> str:
    linhas = [
        " EXTRATO ".center(_LARGURA, "="),
        f"Conta {extrato.numero} - {extrato.titular}",
        "-" * _LARGURA,
    ]
    if not extrato.transacoes:
        linhas.append("Não foram realizadas movimentações.")
    for t in extrato.transacoes:
        sinal = "+" if t.tipo is TipoTransacao.DEPOSITO else "-"
        valor = f"{sinal} {formatar_moeda(t.valor)}"
        linhas.append(
            f"{t.data_hora:%d/%m/%Y %H:%M}  {_ROTULOS[t.tipo]:<9}{valor:>17}"
        )
    linhas += [
        "-" * _LARGURA,
        f"Saldo: {formatar_moeda(extrato.saldo)}",
        "=" * _LARGURA,
    ]
    return "\n".join(linhas)
