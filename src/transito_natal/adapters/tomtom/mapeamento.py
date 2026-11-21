from __future__ import annotations

from datetime import datetime
from typing import Any

from transito_natal.domain.modelos import AmostraTrafego, Segmento
from transito_natal.ports.erros import RespostaInvalida

CAMPOS_OBRIGATORIOS = (
    "currentSpeed",
    "freeFlowSpeed",
    "currentTravelTime",
    "freeFlowTravelTime",
)


def extrair_bloco(payload: dict[str, Any]) -> dict[str, Any]:
    bloco = payload.get("flowSegmentData")
    if not isinstance(bloco, dict):
        raise RespostaInvalida("resposta sem flowSegmentData")
    faltantes = [campo for campo in CAMPOS_OBRIGATORIOS if bloco.get(campo) is None]
    if faltantes:
        raise RespostaInvalida(f"campos ausentes na resposta: {', '.join(faltantes)}")
    return bloco


def comprimento_m(bloco: dict[str, Any]) -> float:
    return float(bloco["freeFlowSpeed"]) * float(bloco["freeFlowTravelTime"]) / 3.6


def para_amostra(
    payload: dict[str, Any],
    segmento: Segmento,
    coletado_em: datetime,
) -> AmostraTrafego:
    bloco = extrair_bloco(payload)
    return AmostraTrafego(
        segmento=segmento.identificador,
        coletado_em=coletado_em,
        velocidade_atual_kmh=float(bloco["currentSpeed"]),
        velocidade_livre_kmh=float(bloco["freeFlowSpeed"]),
        tempo_atual_s=float(bloco["currentTravelTime"]),
        tempo_livre_s=float(bloco["freeFlowTravelTime"]),
        comprimento_m=comprimento_m(bloco),
        confianca=float(bloco.get("confidence", 1.0)),
        via_fechada=bool(bloco.get("roadClosure", False)),
        frc=bloco.get("frc"),
    )
