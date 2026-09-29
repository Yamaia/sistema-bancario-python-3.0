import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from banco.api import criar_app  # noqa: E402
from banco.repositorios import RepositorioMemoria  # noqa: E402
from banco.servicos import ServicoBancario  # noqa: E402


@pytest.fixture
def client(relogio):
    app = criar_app(ServicoBancario(RepositorioMemoria(), relogio=relogio))
    return TestClient(app)


@pytest.fixture
def conta(client) -> int:
    resposta = client.post("/contas", json={"titular": "Maria Silva"})
    assert resposta.status_code == 201
    return resposta.json()["numero"]


def test_saude(client):
    assert client.get("/saude").json() == {"status": "ok"}


def test_abrir_conta(client):
    resposta = client.post("/contas", json={"titular": "Maria Silva"})
    assert resposta.status_code == 201
    assert resposta.json() == {"numero": 1, "titular": "Maria Silva", "saldo": "0.00"}


def test_titular_invalido_retorna_422(client):
    assert client.post("/contas", json={"titular": "A"}).status_code == 422


def test_deposito_e_saque(client, conta):
    dep = client.post(f"/contas/{conta}/depositos", json={"valor": "200.00"})
    assert dep.status_code == 201
    assert dep.json()["tipo"] == "deposito" and dep.json()["saldo_apos"] == "200.00"

    saq = client.post(f"/contas/{conta}/saques", json={"valor": 75.5})
    assert saq.status_code == 201
    assert saq.json()["saldo_apos"] == "124.50"

    assert client.get(f"/contas/{conta}").json()["saldo"] == "124.50"


def test_extrato_e_filtro(client, conta):
    client.post(f"/contas/{conta}/depositos", json={"valor": "100"})
    client.post(f"/contas/{conta}/saques", json={"valor": "30"})

    corpo = client.get(f"/contas/{conta}/extrato").json()
    assert corpo["saldo"] == "70.00"
    assert [t["tipo"] for t in corpo["transacoes"]] == ["deposito", "saque"]

    filtrado = client.get(f"/contas/{conta}/extrato", params={"tipo": "saque"}).json()
    assert [t["tipo"] for t in filtrado["transacoes"]] == ["saque"]


@pytest.mark.parametrize("valor", [0, -5, "abc", "10.005"])
def test_valor_invalido_retorna_422(client, conta, valor):
    assert client.post(f"/contas/{conta}/depositos", json={"valor": valor}).status_code == 422


def test_saldo_insuficiente_retorna_422_com_codigo(client, conta):
    resposta = client.post(f"/contas/{conta}/saques", json={"valor": "10"})
    assert resposta.status_code == 422
    assert resposta.json()["codigo"] == "SaldoInsuficienteError"


def test_limite_por_saque(client, conta):
    client.post(f"/contas/{conta}/depositos", json={"valor": "2000"})
    resposta = client.post(f"/contas/{conta}/saques", json={"valor": "500.01"})
    assert resposta.status_code == 422
    assert resposta.json()["codigo"] == "LimiteSaqueExcedidoError"


def test_limite_de_saques_diarios(client, conta):
    client.post(f"/contas/{conta}/depositos", json={"valor": "1000"})
    for _ in range(3):
        assert client.post(f"/contas/{conta}/saques", json={"valor": "10"}).status_code == 201
    resposta = client.post(f"/contas/{conta}/saques", json={"valor": "10"})
    assert resposta.status_code == 422
    assert resposta.json()["codigo"] == "LimiteSaquesDiariosExcedidoError"


def test_conta_inexistente_retorna_404(client):
    for resposta in (
        client.get("/contas/99"),
        client.get("/contas/99/extrato"),
        client.post("/contas/99/depositos", json={"valor": "10"}),
        client.post("/contas/99/saques", json={"valor": "10"}),
    ):
        assert resposta.status_code == 404
        assert resposta.json()["codigo"] == "ContaNaoEncontradaError"
