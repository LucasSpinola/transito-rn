from __future__ import annotations

import pytest

from tests.fabricas import amostra
from transito_rn.domain.metricas import (
    NivelServico,
    atraso_s,
    atraso_s_por_km,
    congestionado,
    horas_congestionadas,
    indice_buffer,
    indice_planejamento,
    indice_tempo_viagem,
    nivel_servico,
    razao_velocidade,
)


def test_indice_tempo_viagem_igual_razao_inversa_de_velocidade():
    corrida = amostra(velocidade_atual_kmh=25, velocidade_livre_kmh=50)
    assert indice_tempo_viagem(corrida) == pytest.approx(2.0)
    assert razao_velocidade(corrida) == pytest.approx(0.5)


def test_atraso_em_via_livre_e_zero():
    corrida = amostra(velocidade_atual_kmh=50, velocidade_livre_kmh=50)
    assert atraso_s(corrida) == pytest.approx(0.0)


def test_atraso_por_km_normaliza_pelo_comprimento():
    corrida = amostra(velocidade_atual_kmh=30, velocidade_livre_kmh=60, comprimento_m=1000)
    assert atraso_s_por_km(corrida) == pytest.approx(60.0)


@pytest.mark.parametrize(
    ("atual", "livre", "esperado"),
    [
        (50, 50, NivelServico.A),
        (38, 50, NivelServico.B),
        (30, 50, NivelServico.C),
        (22, 50, NivelServico.D),
        (14, 50, NivelServico.E),
        (5, 50, NivelServico.F),
    ],
)
def test_nivel_servico_segue_faixas_de_razao(atual, livre, esperado):
    assert (
        nivel_servico(amostra(velocidade_atual_kmh=atual, velocidade_livre_kmh=livre)) == esperado
    )


def test_via_fechada_conta_como_congestionada():
    corrida = amostra(velocidade_atual_kmh=50, velocidade_livre_kmh=50, via_fechada=True)
    assert congestionado(corrida)


def test_indice_planejamento_usa_percentil_95():
    serie = [float(valor) for valor in range(1, 101)]
    assert indice_planejamento(serie) == pytest.approx(95.05, abs=0.5)


def test_indice_planejamento_ignora_cauda_inferior():
    tranquilo = [1.0] * 90 + [1.1] * 10
    severo = [1.0] * 90 + [4.0] * 10
    assert indice_planejamento(severo) > indice_planejamento(tranquilo)


def test_indice_buffer_zero_em_serie_constante():
    assert indice_buffer([1.5] * 10) == pytest.approx(0.0)


def test_horas_congestionadas_converte_intervalo_em_horas():
    criticas = [amostra(velocidade_atual_kmh=10, velocidade_livre_kmh=50)] * 8
    folgadas = [amostra(velocidade_atual_kmh=50, velocidade_livre_kmh=50)] * 4
    assert horas_congestionadas([*criticas, *folgadas], intervalo_min=15) == pytest.approx(2.0)


def test_serie_vazia_rejeitada():
    with pytest.raises(ValueError, match="serie vazia"):
        indice_planejamento([])
