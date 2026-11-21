from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from matplotlib import pyplot as plt

from transito_rn.domain.metricas import LIMIAR_CONGESTIONAMENTO
from transito_rn.reporting import estilo

Registro = dict[str, Any]
ALTURA_POR_BARRA = 0.42
MAXIMO_DE_SERIES = 5


def _salvar(figura: plt.Figure, destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    figura.savefig(destino)
    plt.close(figura)
    return destino


def _numero(valor: float, casas: int = 2) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def _rotulo(linha: Registro) -> str:
    return f"{linha['via'].replace('Avenida ', 'Av. ')}, {linha['referencia']}"


def ranking(linhas: Sequence[Registro], destino: Path) -> Path:
    estilo.aplicar()
    linhas = list(reversed(linhas))
    altura = max(2.4, len(linhas) * ALTURA_POR_BARRA + 1.4)
    figura, eixo = plt.subplots(figsize=(8.2, altura))

    valores = [linha["indice_medio"] for linha in linhas]
    posicoes = range(len(linhas))
    eixo.barh(
        list(posicoes),
        valores,
        height=0.62,
        color=estilo.SERIES[0],
        zorder=3,
    )
    eixo.axvline(
        LIMIAR_CONGESTIONAMENTO,
        color=estilo.CRITICO,
        linewidth=1.4,
        linestyle=(0, (4, 3)),
        zorder=4,
    )
    eixo.text(
        LIMIAR_CONGESTIONAMENTO,
        len(linhas) - 0.3,
        f" congestionado, {_numero(LIMIAR_CONGESTIONAMENTO, 1)}",
        color=estilo.CRITICO,
        fontsize=8,
        va="center",
    )
    for posicao, valor in zip(posicoes, valores, strict=True):
        eixo.text(
            valor + 0.015,
            posicao,
            _numero(valor),
            va="center",
            fontsize=8,
            color=estilo.TINTA_PRIMARIA,
        )

    eixo.set_yticks(list(posicoes), [_rotulo(linha) for linha in linhas])
    eixo.set_xlabel("Índice de tempo de viagem, média do período")
    eixo.set_xlim(1.0, max([*valores, LIMIAR_CONGESTIONAMENTO]) * 1.12)
    eixo.set_title("Onde o tempo de viagem mais cresce")
    eixo.xaxis.set_major_formatter(lambda valor, _: _numero(valor, 1))
    eixo.xaxis.grid(True)
    eixo.yaxis.grid(False)
    return _salvar(figura, destino)


def perfil_horario(series: dict[str, Sequence[Registro]], destino: Path) -> Path:
    estilo.aplicar()
    figura, eixo = plt.subplots(figsize=(8.2, 4.2))

    for posicao, (nome, linhas) in enumerate(list(series.items())[:MAXIMO_DE_SERIES]):
        horas = [linha["hora"] for linha in linhas]
        indices = [linha["indice_medio"] for linha in linhas]
        cor = estilo.cor_da_serie(posicao)
        eixo.plot(horas, indices, color=cor, label=nome, marker="o", zorder=3)
        eixo.annotate(
            nome,
            (horas[-1], indices[-1]),
            textcoords="offset points",
            xytext=(6, 0),
            fontsize=8,
            color=estilo.TINTA_SECUNDARIA,
            va="center",
        )

    eixo.axhline(
        LIMIAR_CONGESTIONAMENTO,
        color=estilo.CRITICO,
        linewidth=1.4,
        linestyle=(0, (4, 3)),
        zorder=2,
    )
    eixo.set_xlabel("Hora local")
    eixo.set_ylabel("Índice de tempo de viagem")
    eixo.set_xticks(range(0, 24, 2))
    eixo.yaxis.set_major_formatter(lambda valor, _: _numero(valor, 1))
    eixo.set_title("Perfil do dia por segmento")
    eixo.legend(loc="upper left", ncols=2)
    return _salvar(figura, destino)


def mapa_de_calor(linhas: Sequence[Registro], destino: Path) -> Path:
    estilo.aplicar()
    segmentos = sorted({linha["segmento"] for linha in linhas})
    horas = sorted({linha["hora"] for linha in linhas})
    indice = {(linha["segmento"], linha["hora"]): linha["indice_medio"] for linha in linhas}
    grade = [[indice.get((segmento, hora)) for hora in horas] for segmento in segmentos]

    figura, eixo = plt.subplots(figsize=(8.2, max(2.6, len(segmentos) * 0.42 + 1.6)))
    imagem = eixo.imshow(
        grade,
        cmap=estilo.MAPA_SEQUENCIAL,
        aspect="auto",
        vmin=1.0,
        interpolation="nearest",
    )
    eixo.set_xticks(range(len(horas)), [f"{hora}h" for hora in horas])
    eixo.set_yticks(range(len(segmentos)), segmentos)
    eixo.set_title("Índice médio por segmento e hora do dia")
    eixo.grid(False)
    barra = figura.colorbar(imagem, ax=eixo, pad=0.02)
    barra.set_label("Índice de tempo de viagem", color=estilo.TINTA_SECUNDARIA, fontsize=8)
    barra.outline.set_visible(False)
    return _salvar(figura, destino)
