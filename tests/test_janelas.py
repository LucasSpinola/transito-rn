from __future__ import annotations

from datetime import UTC, datetime

from transito_natal.domain.janelas import Janela, classificar, dia_util, em_pico


def momento(hora: int, minuto: int = 0, dia: int = 20) -> datetime:
    return datetime(2026, 11, dia, hora, minuto, tzinfo=UTC)


def test_classifica_pico_da_manha_em_horario_local():
    assert classificar(momento(10)) is Janela.PICO_MANHA


def test_classifica_pico_da_tarde_em_horario_local():
    assert classificar(momento(21)) is Janela.PICO_TARDE


def test_madrugada_fora_de_pico():
    assert not em_pico(momento(6))
    assert classificar(momento(6)) is Janela.MADRUGADA


def test_sabado_nao_e_dia_util():
    assert dia_util(momento(12, dia=20))
    assert not dia_util(momento(12, dia=22))
