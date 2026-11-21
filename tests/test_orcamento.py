from __future__ import annotations

from datetime import UTC, datetime

import pytest

from transito_rn.domain.janelas import Janela
from transito_rn.domain.orcamento import (
    Cadencia,
    ConsumoDoLote,
    Orcamento,
    duracao_minutos,
)


def cadencia_de_pico(intervalo: int = 15, **ajustes: object) -> Cadencia:
    return Cadencia(
        intervalos_min={
            Janela.PICO_MANHA: intervalo,
            Janela.PICO_ALMOCO: intervalo,
            Janela.PICO_TARDE: intervalo,
        },
        **ajustes,
    )


def test_duracao_das_janelas_de_pico():
    assert duracao_minutos(Janela.PICO_MANHA) == 180
    assert duracao_minutos(Janela.PICO_ALMOCO) == 150


def test_coletas_por_dia_soma_apenas_janelas_configuradas():
    assert cadencia_de_pico(15).coletas_por_dia() == 34


def test_cadencia_mais_larga_consome_menos():
    assert cadencia_de_pico(30).coletas_por_dia() < cadencia_de_pico(10).coletas_por_dia()


def test_restricao_a_dias_uteis_reduz_mes():
    assert cadencia_de_pico(15, apenas_dias_uteis=True).coletas_por_mes() < (
        cadencia_de_pico(15).coletas_por_mes()
    )


def test_deve_coletar_apenas_dentro_das_janelas_configuradas():
    cadencia = cadencia_de_pico(15)
    assert cadencia.deve_coletar(datetime(2026, 11, 20, 10, 0, tzinfo=UTC))
    assert not cadencia.deve_coletar(datetime(2026, 11, 20, 6, 0, tzinfo=UTC))


def test_deve_coletar_ignora_fim_de_semana_quando_restrito():
    cadencia = cadencia_de_pico(15, apenas_dias_uteis=True)
    assert not cadencia.deve_coletar(datetime(2026, 11, 22, 10, 0, tzinfo=UTC))


def test_orcamento_dentro_do_teto_tem_folga():
    orcamento = Orcamento(
        consumos=(
            ConsumoDoLote(lote="piloto", segmentos=5, coletas_por_dia=34, requisicoes_por_mes=5270),
        )
    )
    assert orcamento.cabe
    assert orcamento.folga == 11730
    assert orcamento.uso_do_limite == pytest.approx(0.2635)


def test_orcamento_estourado_nao_cabe():
    orcamento = Orcamento(
        consumos=(
            ConsumoDoLote(lote="tudo", segmentos=40, coletas_por_dia=50, requisicoes_por_mes=62000),
        )
    )
    assert not orcamento.cabe
    assert orcamento.folga < 0


def test_vida_restante_cai_conforme_consumo():
    orcamento = Orcamento(
        consumos=(
            ConsumoDoLote(lote="piloto", segmentos=5, coletas_por_dia=34, requisicoes_por_mes=5270),
        )
    )
    assert orcamento.vida_restante(0) > orcamento.vida_restante(10_000)
    assert orcamento.vida_restante(20_000).days == 0


def momento(hora: int, minuto: int = 0, dia: int = 20) -> datetime:
    return datetime(2026, 11, dia, hora, minuto, tzinfo=UTC)


def test_sem_coleta_anterior_coleta_na_primeira_chance():
    assert cadencia_de_pico(15).deve_coletar(momento(10))


def test_execucao_atrasada_pelo_agendador_ainda_coleta():
    cadencia = cadencia_de_pico(15)
    assert cadencia.deve_coletar(momento(10, 23), ultima=momento(9, 45))


def test_execucao_cedo_demais_nao_duplica_amostra():
    cadencia = cadencia_de_pico(15)
    assert not cadencia.deve_coletar(momento(10, 5), ultima=momento(10, 0))


def test_tolerancia_aceita_pequeno_adiantamento():
    cadencia = cadencia_de_pico(15)
    assert cadencia.deve_coletar(momento(10, 14), ultima=momento(9, 59))


def test_relogio_adiantado_na_ultima_coleta_nao_coleta():
    cadencia = cadencia_de_pico(15)
    assert not cadencia.deve_coletar(momento(10), ultima=momento(11))


def test_fora_da_janela_nao_coleta_mesmo_muito_atrasado():
    cadencia = cadencia_de_pico(15)
    assert not cadencia.deve_coletar(momento(6), ultima=momento(1))
