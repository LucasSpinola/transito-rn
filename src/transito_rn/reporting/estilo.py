from __future__ import annotations

from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

SUPERFICIE = "#fcfcfb"
TINTA_PRIMARIA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
TINTA_DISCRETA = "#c3c2b7"

SERIES = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4")
CRITICO = "#d03b3b"

RAMPA_SEQUENCIAL = (
    "#cde2fb",
    "#9ec5f4",
    "#6da7ec",
    "#3987e5",
    "#2a78d6",
    "#256abf",
    "#184f95",
    "#0d366b",
)

MAPA_SEQUENCIAL = LinearSegmentedColormap.from_list("congestionamento", RAMPA_SEQUENCIAL)

PARAMETROS = {
    "figure.facecolor": SUPERFICIE,
    "figure.dpi": 160,
    "axes.facecolor": SUPERFICIE,
    "axes.edgecolor": TINTA_DISCRETA,
    "axes.labelcolor": TINTA_SECUNDARIA,
    "axes.titlecolor": TINTA_PRIMARIA,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.titlepad": 14,
    "axes.labelsize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": TINTA_DISCRETA,
    "grid.alpha": 0.35,
    "grid.linewidth": 0.6,
    "xtick.color": TINTA_SECUNDARIA,
    "ytick.color": TINTA_SECUNDARIA,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "legend.frameon": False,
    "legend.fontsize": 8,
    "legend.labelcolor": TINTA_SECUNDARIA,
    "lines.linewidth": 2.0,
    "lines.markersize": 5,
    "font.size": 9,
    "savefig.facecolor": SUPERFICIE,
    "savefig.bbox": "tight",
}


def aplicar() -> None:
    plt.rcParams.update(PARAMETROS)


def cor_da_serie(posicao: int) -> str:
    return SERIES[posicao % len(SERIES)]
