"""Exceções de domínio.

Toda regra de negócio violada vira uma exceção que herda de `ErroDominio`.
As camadas de fora (API, CLI) decidem como apresentar cada erro.
"""


class ErroDominio(Exception):
    """Base de todos os erros de regra de negócio."""


class ValorInvalidoError(ErroDominio):
    """Valor monetário inválido (não numérico, não positivo ou com mais de 2 casas)."""


class SaldoInsuficienteError(ErroDominio):
    """O saldo não cobre o saque (e a tarifa, se houver)."""


class LimiteSaqueExcedidoError(ErroDominio):
    """O valor pedido ultrapassa o limite por saque."""


class LimiteSaquesDiariosExcedidoError(ErroDominio):
    """A quantidade máxima de saques do dia já foi atingida."""


class ContaNaoEncontradaError(ErroDominio):
    """Não existe conta com o número informado."""


class TitularInvalidoError(ErroDominio):
    """Nome do titular vazio ou fora do tamanho permitido."""
