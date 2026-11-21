from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date, datetime
from typing import Protocol, runtime_checkable

from transito_natal.domain.modelos import AmostraClima, AmostraTrafego, Coordenada, Segmento


@runtime_checkable
class FonteDeTrafego(Protocol):
    def amostrar(self, segmentos: Sequence[Segmento]) -> Iterable[AmostraTrafego]: ...


@runtime_checkable
class FonteDeClima(Protocol):
    def amostrar(self, ponto: Coordenada, momento: datetime) -> AmostraClima: ...


@runtime_checkable
class CatalogoDeSegmentos(Protocol):
    def listar(self) -> Sequence[Segmento]: ...


@runtime_checkable
class RepositorioDeAmostras(Protocol):
    def gravar(self, amostras: Sequence[AmostraTrafego]) -> int: ...

    def gravar_clima(self, amostras: Sequence[AmostraClima]) -> int: ...

    def dias_disponiveis(self) -> Sequence[date]: ...
