from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from tests.fabricas import amostra, segmento
from transito_rn.adapters.armazenamento.parquet import RepositorioParquet
from transito_rn.analytics.analise import Analise
from transito_rn.domain.modelos import AmostraClima

SEGMENTOS = (
    segmento("mlm-cei", referencia="frente ao CEI Zona Sul"),
    segmento("abel-cabral", via="Avenida Abel Cabral", referencia="trecho central"),
)

PERFIL = {
    "mlm-cei": {7: 8.0, 8: 10.0, 10: 18.0, 12: 9.0, 17: 7.0, 21: 30.0},
    "abel-cabral": {7: 26.0, 8: 28.0, 10: 30.0, 12: 27.0, 17: 25.0, 21: 32.0},
}


def semear(raiz, com_chuva: bool = False) -> RepositorioParquet:
    repositorio = RepositorioParquet(raiz)
    for dia in range(16, 21):
        for hora_local in sorted(PERFIL["mlm-cei"]):
            momento = datetime(2026, 11, dia, hora_local, tzinfo=UTC) + timedelta(hours=3)
            repositorio.gravar(
                [
                    amostra(
                        segmento=nome,
                        coletado_em=momento,
                        velocidade_atual_kmh=perfil[hora_local],
                        velocidade_livre_kmh=35.0,
                    )
                    for nome, perfil in PERFIL.items()
                ]
            )
            if com_chuva:
                repositorio.gravar_clima(
                    [
                        AmostraClima(
                            coletado_em=momento,
                            chuva_mm=12.0 if hora_local == 17 else 0.0,
                            temperatura_c=28.0,
                            vento_kmh=12.0,
                        )
                    ]
                )
    return repositorio


@pytest.fixture
def analise(tmp_path):
    semear(tmp_path)
    with Analise(tmp_path, SEGMENTOS) as instancia:
        yield instancia


def test_base_sem_amostras_nao_quebra(tmp_path):
    with Analise(tmp_path, SEGMENTOS) as instancia:
        assert instancia.vazio
        assert instancia.ranking_de_gargalos() == []
        assert instancia.cobertura()["amostras"] == 0


def test_cobertura_conta_dias_e_segmentos(analise):
    cobertura = analise.cobertura()
    assert cobertura["segmentos"] == 2
    assert cobertura["dias"] == 5
    assert cobertura["amostras"] == 60


def test_ranking_coloca_o_segmento_da_escola_no_topo(analise):
    ranking = analise.ranking_de_gargalos()
    assert [linha["segmento"] for linha in ranking] == ["mlm-cei", "abel-cabral"]
    assert ranking[0]["indice_medio"] > ranking[1]["indice_medio"]
    assert ranking[0]["percentual_critico"] > ranking[1]["percentual_critico"]


def test_ranking_traz_metadados_do_catalogo(analise):
    topo = analise.ranking_de_gargalos()[0]
    assert topo["via"] == "Avenida Maria Lacerda Montenegro"
    assert topo["municipio"] == "Parnamirim"
    assert topo["bairro"] == "Nova Parnamirim"


def test_ranking_respeita_minimo_de_amostras(analise):
    assert analise.ranking_de_gargalos(minimo_de_amostras=999) == []


def test_perfil_por_janela_identifica_o_pior_pico(analise):
    perfil = analise.perfil_por_janela()
    assert perfil[0]["janela"] == "pico_tarde"
    assert {linha["janela"] for linha in perfil} >= {"pico_manha", "pico_almoco", "pico_tarde"}


def test_perfil_por_hora_usa_horario_local(analise):
    horas = {linha["hora"] for linha in analise.perfil_por_hora()}
    assert horas == {7, 8, 10, 12, 17, 21}


def test_perfil_por_hora_filtra_por_segmento(analise):
    geral = analise.perfil_por_hora()
    filtrado = analise.perfil_por_hora("mlm-cei")
    assert sum(linha["amostras"] for linha in filtrado) * 2 == sum(
        linha["amostras"] for linha in geral
    )


def test_perfil_por_dia_da_semana_cobre_a_semana_util(analise):
    perfil = analise.perfil_por_dia_da_semana()
    assert [linha["dia_da_semana"] for linha in perfil] == [1, 2, 3, 4, 5]


def test_mapa_de_calor_cruza_segmento_com_hora(analise):
    assert len(analise.mapa_de_calor()) == 12


def test_piores_momentos_vem_ordenado_pelo_indice(analise):
    momentos = analise.piores_momentos(limite=3)
    assert len(momentos) == 3
    assert momentos[0]["indice"] >= momentos[-1]["indice"]
    assert momentos[0]["nivel"] == "F"


def test_efeito_da_chuva_compara_os_dois_estados(tmp_path):
    semear(tmp_path, com_chuva=True)
    with Analise(tmp_path, SEGMENTOS) as instancia:
        efeito = instancia.efeito_da_chuva()
    assert [linha["chovendo"] for linha in efeito] == [False, True]
    chuva = next(linha for linha in efeito if linha["chovendo"])
    seco = next(linha for linha in efeito if not linha["chovendo"])
    assert chuva["indice_medio"] > seco["indice_medio"]


def test_ranking_desempata_de_forma_estavel(tmp_path):
    semear(tmp_path)
    ordens = []
    for _ in range(3):
        with Analise(tmp_path, SEGMENTOS) as instancia:
            ordens.append([linha["segmento"] for linha in instancia.ranking_de_gargalos()])
    assert ordens[0] == ordens[1] == ordens[2]


def test_piores_momentos_desempatam_de_forma_estavel(analise):
    primeiro = analise.piores_momentos(limite=10)
    segundo = analise.piores_momentos(limite=10)
    assert [linha["momento"] for linha in primeiro] == [linha["momento"] for linha in segundo]
