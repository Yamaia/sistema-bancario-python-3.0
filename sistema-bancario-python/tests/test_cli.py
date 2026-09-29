from banco.cli import executar
from banco.repositorios import RepositorioMemoria
from banco.servicos import ServicoBancario


def rodar(relogio, *respostas: str) -> str:
    servico = ServicoBancario(RepositorioMemoria(), relogio=relogio)
    fila = iter(respostas)
    saidas: list[str] = []
    executar(servico, entrada=lambda _prompt: next(fila), saida=saidas.append)
    return "\n".join(saidas)


def test_fluxo_basico(relogio):
    texto = rodar(relogio, "n", "Maria Silva", "d", "1.000,50", "s", "200", "e", "q")
    assert "Conta 1 criada com sucesso." in texto
    assert "Depósito de R$ 1.000,50 realizado." in texto
    assert "Saque de R$ 200,00 realizado." in texto
    assert "Saldo: R$ 800,50" in texto
    assert "15/03/2026 10:00" in texto


def test_erros_sao_mostrados_sem_derrubar_o_programa(relogio):
    texto = rodar(relogio, "n", "Maria", "s", "50", "d", "abc", "x", "q")
    assert "Operação não realizada: Saldo insuficiente" in texto
    assert "Operação não realizada: Valor inválido." in texto
    assert "Opção inválida" in texto
    assert texto.endswith("Até logo!")


def test_conta_inexistente_e_numero_invalido(relogio):
    texto = rodar(relogio, "7", "abc", "q")
    assert "Conta 7 não encontrada." in texto
    assert "Digite um número de conta válido." in texto


def test_extrato_vazio(relogio):
    texto = rodar(relogio, "n", "Maria", "e", "q")
    assert "Não foram realizadas movimentações." in texto
