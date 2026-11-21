from __future__ import annotations

from datetime import UTC, date, datetime

from tests.fabricas import amostra
from transito_rn.adapters.armazenamento.parquet import RepositorioParquet
from transito_rn.domain.modelos import AmostraClima


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


def test_sem_dados_nao_ha_ultima_coleta(tmp_path):
    assert RepositorioParquet(tmp_path).ultima_coleta_por_lote() == {}


def test_ultima_coleta_separa_por_lote(tmp_path):
    repositorio = RepositorioParquet(tmp_path)
    repositorio.gravar(
        [
            amostra(
                segmento="mlm-cei",
                lote="parnamirim-cei",
                coletado_em=datetime(2026, 11, 21, 10, 0, tzinfo=UTC),
            ),
            amostra(
                segmento="roberto-freire",
                lote="natal-zona-sul",
                coletado_em=datetime(2026, 11, 21, 10, 0, tzinfo=UTC),
            ),
        ]
    )
    repositorio.gravar(
        [
            amostra(
                segmento="mlm-cei",
                lote="parnamirim-cei",
                coletado_em=datetime(2026, 11, 21, 10, 15, tzinfo=UTC),
            )
        ]
    )
    ultimas = repositorio.ultima_coleta_por_lote()
    assert ultimas["parnamirim-cei"] == datetime(2026, 11, 21, 10, 15, tzinfo=UTC)
    assert ultimas["natal-zona-sul"] == datetime(2026, 11, 21, 10, 0, tzinfo=UTC)


def test_amostra_sem_lote_nao_entra_no_registro(tmp_path):
    repositorio = RepositorioParquet(tmp_path)
    repositorio.gravar([amostra(coletado_em=datetime(2026, 11, 21, 10, 0, tzinfo=UTC))])
    assert repositorio.ultima_coleta_por_lote() == {}


def test_parquet_antigo_sem_coluna_de_lote_nao_quebra(tmp_path):
    import pyarrow as pa
    import pyarrow.parquet as pq

    destino = tmp_path / "trafego" / "dt=2026-11-21"
    destino.mkdir(parents=True)
    antigo = pa.table(
        {
            "segmento": ["mlm-cei"],
            "coletado_em": pa.array(
                [datetime(2026, 11, 21, 10, 0, tzinfo=UTC)], pa.timestamp("us", tz="UTC")
            ),
        }
    )
    pq.write_table(antigo, destino / "100000.parquet")
    assert RepositorioParquet(tmp_path).ultima_coleta_por_lote() == {}
