from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict

from transito_rn.domain.modelos import Segmento
from transito_rn.domain.orcamento import (
    LIMITE_MENSAL_PADRAO,
    MARGEM_DE_SEGURANCA,
    Cadencia,
    ConsumoDoLote,
    Orcamento,
)


class Lote(BaseModel):
    model_config = ConfigDict(frozen=True)

    identificador: str
    descricao: str
    ativo: bool
    cadencia: Cadencia
    segmentos: tuple[Segmento, ...]

    def consumo(self) -> ConsumoDoLote:
        return ConsumoDoLote(
            lote=self.identificador,
            segmentos=len(self.segmentos),
            coletas_por_dia=self.cadencia.coletas_por_dia(),
            requisicoes_por_mes=self.cadencia.coletas_por_mes() * len(self.segmentos),
        )


class Catalogo(BaseModel):
    model_config = ConfigDict(frozen=True)

    limite_mensal: int = LIMITE_MENSAL_PADRAO
    margem: float = MARGEM_DE_SEGURANCA
    lotes: tuple[Lote, ...]

    def listar(self) -> Sequence[Segmento]:
        return tuple(segmento for lote in self.lotes if lote.ativo for segmento in lote.segmentos)

    def listar_tudo(self) -> Sequence[Segmento]:
        return tuple(segmento for lote in self.lotes for segmento in lote.segmentos)

    def lote(self, identificador: str) -> Lote:
        for lote in self.lotes:
            if lote.identificador == identificador:
                return lote
        raise KeyError(f"lote inexistente: {identificador}")

    def a_coletar(self, momento: datetime) -> Sequence[Segmento]:
        return tuple(
            segmento
            for lote in self.lotes
            if lote.ativo and lote.cadencia.deve_coletar(momento)
            for segmento in lote.segmentos
        )

    def orcamento(self, apenas_ativos: bool = True) -> Orcamento:
        lotes = [lote for lote in self.lotes if lote.ativo or not apenas_ativos]
        return Orcamento(
            limite_mensal=self.limite_mensal,
            margem=self.margem,
            consumos=tuple(lote.consumo() for lote in lotes),
        )


def carregar(caminho: Path) -> Catalogo:
    bruto = yaml.safe_load(caminho.read_text(encoding="utf-8"))
    for lote in bruto.get("lotes", []):
        for segmento in lote.get("segmentos", []):
            segmento["lote"] = lote["identificador"]
    return Catalogo.model_validate(bruto)
