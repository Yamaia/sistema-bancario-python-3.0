from datetime import datetime, timedelta

import pytest

from banco.repositorios import RepositorioMemoria, RepositorioSQLite
from banco.servicos import ServicoBancario


class RelogioFalso:
    """Relógio controlável: os testes decidem que dia e hora são."""

    def __init__(self, inicio: datetime = datetime(2026, 3, 15, 10, 0)) -> None:
        self.agora = inicio

    def __call__(self) -> datetime:
        return self.agora

    def avancar(self, **kwargs) -> None:
        self.agora += timedelta(**kwargs)


@pytest.fixture
def relogio() -> RelogioFalso:
    return RelogioFalso()


@pytest.fixture(params=["memoria", "sqlite"])
def repositorio(request):
    repo = RepositorioMemoria() if request.param == "memoria" else RepositorioSQLite()
    yield repo
    if hasattr(repo, "fechar"):
        repo.fechar()


@pytest.fixture
def servico(repositorio, relogio) -> ServicoBancario:
    return ServicoBancario(repositorio, relogio=relogio)
