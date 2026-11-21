from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from transito_rn.adapters.armazenamento.catalogo_yaml import carregar

CAMINHO = Path("config/segmentos.yaml")


@pytest.fixture(scope="module")
def catalogo():
    return carregar(CAMINHO)


def test_cobre_as_quatro_zonas_de_natal_e_o_interior(catalogo):
    assert [lote.identificador for lote in catalogo.lotes] == [
        "parnamirim-cei",
        "natal-zona-sul",
        "natal-zona-leste",
        "natal-zona-norte",
        "natal-zona-oeste",
        "regiao-metropolitana",
        "mossoro",
        "acessos-rodoviarios",
    ]


def test_apenas_o_lote_piloto_comeca_ativo(catalogo):
    assert [lote.identificador for lote in catalogo.lotes if lote.ativo] == ["parnamirim-cei"]
    assert len(catalogo.listar()) == 3
    assert len(catalogo.listar_tudo()) == 37


def test_identificadores_sao_unicos(catalogo):
    identificadores = [segmento.identificador for segmento in catalogo.listar_tudo()]
    assert len(identificadores) == len(set(identificadores))


def test_cobre_os_municipios_que_importam(catalogo):
    municipios = {segmento.municipio for segmento in catalogo.listar_tudo()}
    assert {"Natal", "Parnamirim", "Mossoró", "Macaíba", "São Gonçalo do Amarante"} <= municipios


def test_segmento_herda_o_lote_de_origem(catalogo):
    segmentos = {segmento.identificador: segmento for segmento in catalogo.listar_tudo()}
    assert segmentos["mlm-cei"].lote == "parnamirim-cei"
    assert segmentos["ponte-newton-navarro"].lote == "natal-zona-norte"
    assert segmentos["mossoro-dutra"].lote == "mossoro"


def test_orcamento_dos_ativos_cabe_no_limite(catalogo):
    orcamento = catalogo.orcamento()
    assert orcamento.cabe
    assert orcamento.requisicoes_por_mes < catalogo.limite_mensal


def test_orcamento_de_todos_os_lotes_tambem_cabe(catalogo):
    orcamento = catalogo.orcamento(apenas_ativos=False)
    assert orcamento.cabe, f"projecao de {orcamento.requisicoes_por_mes} estoura o teto"


def test_coleta_fora_de_janela_nao_seleciona_segmento(catalogo):
    assert catalogo.a_coletar(datetime(2026, 11, 20, 6, 0, tzinfo=UTC)) == ()


def test_coleta_em_pico_seleciona_o_lote_ativo(catalogo):
    selecionados = catalogo.a_coletar(datetime(2026, 11, 20, 10, 0, tzinfo=UTC))
    assert len(selecionados) == 3


def test_lote_inexistente_levanta_erro(catalogo):
    with pytest.raises(KeyError, match="lote inexistente"):
        catalogo.lote("zona-leste")
