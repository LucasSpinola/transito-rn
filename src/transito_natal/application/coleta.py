from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import NamedTuple

from transito_natal.domain.modelos import AmostraClima, AmostraTrafego, Segmento
from transito_natal.ports.erros import ErroDeColeta, LimiteDeRequisicoesExcedido
from transito_natal.ports.fontes import (
    FonteDeClima,
    FonteDeTrafego,
    RepositorioDeAmostras,
)


class Falha(NamedTuple):
    segmento: str
    motivo: str


class ResultadoDaColeta(NamedTuple):
    momento: datetime
    consultados: int
    gravados: int
    clima_gravado: bool
    falhas: tuple[Falha, ...]
    interrompida_por_limite: bool

    @property
    def completa(self) -> bool:
        return not self.falhas and not self.interrompida_por_limite


class ExecutarColeta:
    def __init__(
        self,
        fonte_trafego: FonteDeTrafego,
        repositorio: RepositorioDeAmostras,
        fonte_clima: FonteDeClima | None = None,
    ) -> None:
        self._trafego = fonte_trafego
        self._repositorio = repositorio
        self._clima = fonte_clima

    def executar(self, segmentos: Sequence[Segmento], momento: datetime) -> ResultadoDaColeta:
        amostras: list[AmostraTrafego] = []
        falhas: list[Falha] = []
        interrompida = False

        for segmento in segmentos:
            try:
                amostras.append(self._trafego.amostrar(segmento))
            except LimiteDeRequisicoesExcedido:
                interrompida = True
                break
            except ErroDeColeta as erro:
                falhas.append(Falha(segmento.identificador, str(erro)))

        gravados = self._repositorio.gravar(amostras)
        clima_gravado = self._coletar_clima(segmentos, momento)

        return ResultadoDaColeta(
            momento=momento,
            consultados=len(segmentos),
            gravados=gravados,
            clima_gravado=clima_gravado,
            falhas=tuple(falhas),
            interrompida_por_limite=interrompida,
        )

    def _coletar_clima(self, segmentos: Sequence[Segmento], momento: datetime) -> bool:
        if self._clima is None or not segmentos:
            return False
        try:
            amostra: AmostraClima = self._clima.amostrar(segmentos[0].ponto, momento)
        except ErroDeColeta:
            return False
        return self._repositorio.gravar_clima([amostra]) > 0
