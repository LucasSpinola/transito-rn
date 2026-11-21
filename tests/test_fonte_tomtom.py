from __future__ import annotations

import httpx
import pytest
import respx

from tests.fabricas import segmento
from transito_natal.adapters.tomtom.cliente import BASE_URL, FonteTomTom
from transito_natal.adapters.tomtom.mapeamento import comprimento_m, extrair_bloco, para_amostra
from transito_natal.domain.metricas import indice_tempo_viagem
from transito_natal.ports.erros import (
    FonteIndisponivel,
    LimiteDeRequisicoesExcedido,
    RespostaInvalida,
)

RESPOSTA = {
    "flowSegmentData": {
        "frc": "FRC6",
        "currentSpeed": 30,
        "freeFlowSpeed": 35,
        "currentTravelTime": 411,
        "freeFlowTravelTime": 352,
        "confidence": 1,
        "roadClosure": False,
    }
}


def fonte(**ajustes: object) -> FonteTomTom:
    return FonteTomTom(chave="chave-de-teste", qps=0, **ajustes)


def test_chave_vazia_rejeitada():
    with pytest.raises(ValueError, match="chave da api"):
        FonteTomTom(chave="")


def test_comprimento_derivado_do_fluxo_livre():
    assert comprimento_m(RESPOSTA["flowSegmentData"]) == pytest.approx(3422.2, abs=0.5)


def test_resposta_sem_bloco_de_fluxo_e_invalida():
    with pytest.raises(RespostaInvalida, match="flowSegmentData"):
        extrair_bloco({"erro": "nada aqui"})


def test_resposta_com_campo_ausente_e_invalida():
    with pytest.raises(RespostaInvalida, match="campos ausentes"):
        extrair_bloco({"flowSegmentData": {"currentSpeed": 30}})


def test_mapeamento_preserva_indice_de_tempo_de_viagem():
    from datetime import UTC, datetime

    amostra = para_amostra(RESPOSTA, segmento(), datetime(2026, 11, 20, 10, 0, tzinfo=UTC))
    assert amostra.segmento == "mlm-cei"
    assert amostra.frc == "FRC6"
    assert indice_tempo_viagem(amostra) == pytest.approx(411 / 352)


@respx.mock
def test_amostragem_consulta_um_endpoint_por_segmento():
    rota = respx.get(url__startswith=BASE_URL).mock(return_value=httpx.Response(200, json=RESPOSTA))
    with fonte() as origem:
        amostras = list(origem.amostrar([segmento("a"), segmento("b")]))
    assert [item.segmento for item in amostras] == ["a", "b"]
    assert rota.call_count == 2
    assert origem.requisicoes == 2


@respx.mock
def test_zoom_do_segmento_vai_na_url():
    rota = respx.get(url__startswith=BASE_URL).mock(return_value=httpx.Response(200, json=RESPOSTA))
    with fonte() as origem:
        list(origem.amostrar([segmento("a", zoom=12)]))
    assert "/absolute/12/json" in str(rota.calls[0].request.url)


@respx.mock
def test_excesso_de_requisicoes_interrompe_sem_retentativa():
    rota = respx.get(url__startswith=BASE_URL).mock(return_value=httpx.Response(429))
    with pytest.raises(LimiteDeRequisicoesExcedido), fonte() as origem:
        list(origem.amostrar([segmento()]))
    assert rota.call_count == 1


@respx.mock
def test_erro_de_servidor_dispara_retentativa_limitada():
    rota = respx.get(url__startswith=BASE_URL).mock(return_value=httpx.Response(503))
    with pytest.raises(FonteIndisponivel), fonte() as origem:
        list(origem.amostrar([segmento()]))
    assert rota.call_count == 3


@respx.mock
def test_retentativa_recupera_apos_falha_transitoria():
    respx.get(url__startswith=BASE_URL).mock(
        side_effect=[httpx.Response(503), httpx.Response(200, json=RESPOSTA)]
    )
    with fonte() as origem:
        amostras = list(origem.amostrar([segmento()]))
    assert len(amostras) == 1
