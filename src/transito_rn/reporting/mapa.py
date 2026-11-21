from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import folium

from transito_rn.domain.metricas import LIMIAR_CONGESTIONAMENTO
from transito_rn.domain.modelos import Segmento
from transito_rn.reporting import estilo

Registro = dict[str, Any]
CENTRO = (-5.83, -35.22)
ZOOM_INICIAL = 12
FAIXAS_DE_COR = ((1.05, 0), (1.15, 2), (LIMIAR_CONGESTIONAMENTO, 4), (1.6, 6))


def _cor(indice: float) -> str:
    for limite, passo in FAIXAS_DE_COR:
        if indice < limite:
            return estilo.RAMPA_SEQUENCIAL[passo]
    return estilo.CRITICO


def _raio(indice: float) -> float:
    return 6 + min(max(indice - 1, 0), 1) * 14


def desenhar(
    linhas: Sequence[Registro],
    segmentos: Sequence[Segmento],
    destino: Path,
) -> Path:
    pontos = {segmento.identificador: segmento for segmento in segmentos}
    mapa = folium.Map(location=CENTRO, zoom_start=ZOOM_INICIAL, tiles="OpenStreetMap")

    for linha in linhas:
        segmento = pontos.get(linha["segmento"])
        if segmento is None:
            continue
        indice = float(linha["indice_medio"])
        descricao = (
            f"<b>{segmento.via}</b><br>{segmento.referencia}<br>"
            f"{segmento.bairro}, {segmento.municipio}<br><br>"
            f"índice médio {indice:.2f}<br>"
            f"índice no percentil 95 {linha['indice_p95']:.2f}<br>"
            f"atraso médio {linha['atraso_medio_s_km']:.0f} s/km<br>"
            f"{linha['percentual_critico']:.0f}% das amostras em congestionamento<br>"
            f"{linha['amostras']} amostras"
        )
        folium.CircleMarker(
            location=(segmento.ponto.latitude, segmento.ponto.longitude),
            radius=_raio(indice),
            color=estilo.SUPERFICIE,
            weight=2,
            fill=True,
            fill_color=_cor(indice),
            fill_opacity=0.85,
            tooltip=f"{segmento.identificador}, índice {indice:.2f}",
            popup=folium.Popup(descricao, max_width=280),
        ).add_to(mapa)

    destino.parent.mkdir(parents=True, exist_ok=True)
    mapa.save(str(destino))
    return destino
