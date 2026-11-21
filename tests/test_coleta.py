from __future__ import annotations

from datetime import UTC, datetime

from tests.duplos import ClimaFalso, ErroQualquer, RepositorioFalso, TrafegoFalso
from tests.fabricas import segmento
from transito_rn.application.coleta import ExecutarColeta
from transito_rn.ports.erros import FonteIndisponivel, LimiteDeRequisicoesExcedido

MOMENTO = datetime(2026, 11, 20, 10, 0, tzinfo=UTC)
SEGMENTOS = (segmento("mlm-cei"), segmento("abel-cabral"), segmento("ayrton-senna"))


def test_coleta_completa_grava_tudo():
    repositorio = RepositorioFalso()
    clima = ClimaFalso()
    resultado = ExecutarColeta(TrafegoFalso(), repositorio, clima).executar(SEGMENTOS, MOMENTO)
    assert resultado.completa
    assert resultado.gravados == 3
    assert resultado.clima_gravado
    assert clima.chamadas == 1


def test_falha_em_um_segmento_nao_derruba_os_demais():
    trafego = TrafegoFalso(falhas={"abel-cabral": FonteIndisponivel("fonte fora do ar")})
    repositorio = RepositorioFalso()
    resultado = ExecutarColeta(trafego, repositorio).executar(SEGMENTOS, MOMENTO)
    assert resultado.gravados == 2
    assert [falha.segmento for falha in resultado.falhas] == ["abel-cabral"]
    assert not resultado.completa
    assert trafego.consultados == ["mlm-cei", "abel-cabral", "ayrton-senna"]


def test_limite_de_requisicoes_interrompe_a_rodada():
    trafego = TrafegoFalso(falhas={"abel-cabral": LimiteDeRequisicoesExcedido("cota esgotada")})
    resultado = ExecutarColeta(trafego, RepositorioFalso()).executar(SEGMENTOS, MOMENTO)
    assert resultado.interrompida_por_limite
    assert resultado.gravados == 1
    assert trafego.consultados == ["mlm-cei", "abel-cabral"]


def test_amostras_parciais_sao_preservadas_apos_o_limite():
    trafego = TrafegoFalso(falhas={"mlm-cei": LimiteDeRequisicoesExcedido("cota esgotada")})
    repositorio = RepositorioFalso()
    resultado = ExecutarColeta(trafego, repositorio).executar(SEGMENTOS, MOMENTO)
    assert resultado.gravados == 0
    assert repositorio.trafego == []


def test_falha_de_clima_nao_invalida_o_trafego():
    clima = ClimaFalso(erro=ErroQualquer("sem clima"))
    resultado = ExecutarColeta(TrafegoFalso(), RepositorioFalso(), clima).executar(
        SEGMENTOS, MOMENTO
    )
    assert resultado.gravados == 3
    assert not resultado.clima_gravado


def test_sem_segmentos_nao_consulta_clima():
    clima = ClimaFalso()
    resultado = ExecutarColeta(TrafegoFalso(), RepositorioFalso(), clima).executar((), MOMENTO)
    assert resultado.consultados == 0
    assert clima.chamadas == 0
