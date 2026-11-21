from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum
from statistics import mean, quantiles

from transito_rn.domain.modelos import AmostraTrafego

LIMIARES_NIVEL_SERVICO = ((0.85, "A"), (0.70, "B"), (0.55, "C"), (0.40, "D"), (0.25, "E"))
LIMIAR_CONGESTIONAMENTO = 1.3


class NivelServico(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"


def indice_tempo_viagem(amostra: AmostraTrafego) -> float:
    return amostra.tempo_atual_s / amostra.tempo_livre_s


def razao_velocidade(amostra: AmostraTrafego) -> float:
    return amostra.velocidade_atual_kmh / amostra.velocidade_livre_kmh


def atraso_s(amostra: AmostraTrafego) -> float:
    return max(amostra.tempo_atual_s - amostra.tempo_livre_s, 0.0)


def atraso_s_por_km(amostra: AmostraTrafego) -> float:
    return atraso_s(amostra) / (amostra.comprimento_m / 1000)


def nivel_servico(amostra: AmostraTrafego) -> NivelServico:
    razao = razao_velocidade(amostra)
    for limiar, rotulo in LIMIARES_NIVEL_SERVICO:
        if razao >= limiar:
            return NivelServico(rotulo)
    return NivelServico.F


def congestionado(amostra: AmostraTrafego, limiar: float = LIMIAR_CONGESTIONAMENTO) -> bool:
    return amostra.via_fechada or indice_tempo_viagem(amostra) >= limiar


def percentil(valores: Sequence[float], posicao: float) -> float:
    if not valores:
        raise ValueError("serie vazia")
    if len(valores) == 1:
        return float(valores[0])
    cortes = quantiles(sorted(valores), n=100, method="inclusive")
    return float(cortes[min(max(int(posicao) - 1, 0), len(cortes) - 1)])


def indice_planejamento(indices: Sequence[float]) -> float:
    return percentil(indices, 95)


def indice_buffer(indices: Sequence[float]) -> float:
    if not indices:
        raise ValueError("serie vazia")
    media = mean(indices)
    if media == 0:
        raise ValueError("media nula")
    return (percentil(indices, 95) - media) / media


def horas_congestionadas(
    amostras: Sequence[AmostraTrafego],
    intervalo_min: float,
    limiar: float = LIMIAR_CONGESTIONAMENTO,
) -> float:
    criticas = sum(1 for amostra in amostras if congestionado(amostra, limiar))
    return criticas * intervalo_min / 60
