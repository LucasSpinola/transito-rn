from __future__ import annotations

from datetime import datetime, time
from enum import StrEnum
from zoneinfo import ZoneInfo

FUSO_LOCAL = ZoneInfo("America/Fortaleza")


class Janela(StrEnum):
    PICO_MANHA = "pico_manha"
    ENTREPICO_MANHA = "entrepico_manha"
    PICO_ALMOCO = "pico_almoco"
    ENTREPICO_TARDE = "entrepico_tarde"
    PICO_TARDE = "pico_tarde"
    NOITE = "noite"
    MADRUGADA = "madrugada"


FAIXAS: tuple[tuple[Janela, time, time], ...] = (
    (Janela.MADRUGADA, time(0, 0), time(5, 30)),
    (Janela.PICO_MANHA, time(5, 30), time(8, 30)),
    (Janela.ENTREPICO_MANHA, time(8, 30), time(11, 0)),
    (Janela.PICO_ALMOCO, time(11, 0), time(13, 30)),
    (Janela.ENTREPICO_TARDE, time(13, 30), time(16, 30)),
    (Janela.PICO_TARDE, time(16, 30), time(19, 30)),
    (Janela.NOITE, time(19, 30), time(23, 59, 59)),
)

JANELAS_DE_PICO = frozenset({Janela.PICO_MANHA, Janela.PICO_ALMOCO, Janela.PICO_TARDE})


def momento_local(momento: datetime) -> datetime:
    return momento.astimezone(FUSO_LOCAL)


def classificar(momento: datetime) -> Janela:
    hora = momento_local(momento).time()
    for janela, inicio, fim in FAIXAS:
        if inicio <= hora < fim:
            return janela
    return Janela.NOITE


def em_pico(momento: datetime) -> bool:
    return classificar(momento) in JANELAS_DE_PICO


def dia_util(momento: datetime) -> bool:
    return momento_local(momento).weekday() < 5
