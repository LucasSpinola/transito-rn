from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from tests.fabricas import amostra
from transito_natal.domain.modelos import AmostraClima, AmostraTrafego, Coordenada, Segmento
from transito_natal.ports.erros import ErroDeColeta


class TrafegoFalso:
    def __init__(self, falhas: dict[str, Exception] | None = None) -> None:
        self.falhas = falhas or {}
        self.consultados: list[str] = []

    def amostrar(self, segmento: Segmento) -> AmostraTrafego:
        self.consultados.append(segmento.identificador)
        falha = self.falhas.get(segmento.identificador)
        if falha is not None:
            raise falha
        return amostra(segmento=segmento.identificador)


class ClimaFalso:
    def __init__(self, erro: Exception | None = None) -> None:
        self.erro = erro
        self.chamadas = 0

    def amostrar(self, ponto: Coordenada, momento: datetime) -> AmostraClima:
        self.chamadas += 1
        if self.erro is not None:
            raise self.erro
        return AmostraClima(
            coletado_em=momento,
            chuva_mm=0.0,
            temperatura_c=30.6,
            vento_kmh=14.4,
        )


class RepositorioFalso:
    def __init__(self) -> None:
        self.trafego: list[AmostraTrafego] = []
        self.clima: list[AmostraClima] = []

    def gravar(self, amostras: Sequence[AmostraTrafego]) -> int:
        self.trafego.extend(amostras)
        return len(amostras)

    def gravar_clima(self, amostras: Sequence[AmostraClima]) -> int:
        self.clima.extend(amostras)
        return len(amostras)

    def dias_disponiveis(self) -> Sequence[object]:
        return ()


class ErroQualquer(ErroDeColeta):
    pass
