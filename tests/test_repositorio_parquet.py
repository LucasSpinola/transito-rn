from __future__ import annotations

from datetime import UTC, date, datetime

from tests.fabricas import amostra
from transito_natal.adapters.armazenamento.parquet import RepositorioParquet
from transito_natal.domain.modelos import AmostraClima


def test_gravacao_vazia_nao_cria_arquivo(tmp_path):
    repositorio = RepositorioParquet(tmp_path)
    assert repositorio.gravar([]) == 0
    assert repositorio.dias_disponiveis() == ()


def test_gravacao_particiona_por_dia(tmp_path):
    repositorio = RepositorioParquet(tmp_path)
    repositorio.gravar([amostra(coletado_em=datetime(2026, 11, 20, 10, 0, tzinfo=UTC))])
    repositorio.gravar([amostra(coletado_em=datetime(2026, 11, 21, 10, 0, tzinfo=UTC))])
    assert repositorio.dias_disponiveis() == (date(2026, 11, 20), date(2026, 11, 21))
    assert repositorio.total_de_amostras() == 2


def test_duas_coletas_no_mesmo_dia_nao_se_sobrescrevem(tmp_path):
    repositorio = RepositorioParquet(tmp_path)
    repositorio.gravar([amostra(coletado_em=datetime(2026, 11, 20, 10, 0, tzinfo=UTC))])
    repositorio.gravar([amostra(coletado_em=datetime(2026, 11, 20, 10, 15, tzinfo=UTC))])
    assert repositorio.dias_disponiveis() == (date(2026, 11, 20),)
    assert repositorio.total_de_amostras() == 2


def test_clima_vai_para_conjunto_separado(tmp_path):
    repositorio = RepositorioParquet(tmp_path)
    gravadas = repositorio.gravar_clima(
        [
            AmostraClima(
                coletado_em=datetime(2026, 11, 20, 10, 0, tzinfo=UTC),
                chuva_mm=12.4,
                temperatura_c=27.1,
                vento_kmh=18.0,
            )
        ]
    )
    assert gravadas == 1
    assert (tmp_path / "clima" / "dt=2026-11-20").exists()
    assert repositorio.total_de_amostras() == 0
