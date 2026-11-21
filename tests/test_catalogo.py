from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from transito_natal.adapters.armazenamento.catalogo_yaml import carregar

CAMINHO = Path("config/segmentos.yaml")


@pytest.fixture(scope="module")
def catalogo():
    return carregar(CAMINHO)


def test_carrega_tres_lotes(catalogo):
    assert [lote.identificador for lote in catalogo.lotes] == [
        "nova-parnamirim",
        "natal-zona-sul",
        "natal-zona-norte",
    ]


def test_apenas_o_lote_piloto_comeca_ativo(catalogo):
    assert [lote.identificador for lote in catalogo.lotes if lote.ativo] == ["nova-parnamirim"]
    assert len(catalogo.listar()) == 5
    assert len(catalogo.listar_tudo()) == 19


def test_segmento_herda_o_lote_de_origem(catalogo):
    segmentos = {segmento.identificador: segmento for segmento in catalogo.listar_tudo()}
    assert segmentos["mlm-cei"].lote == "nova-parnamirim"
    assert segmentos["ponte-newton-navarro"].lote == "natal-zona-norte"


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
    assert len(selecionados) == 5


def test_lote_inexistente_levanta_erro(catalogo):
    with pytest.raises(KeyError, match="lote inexistente"):
        catalogo.lote("zona-leste")
