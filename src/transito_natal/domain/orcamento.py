from __future__ import annotations

from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field

from transito_natal.domain.janelas import FAIXAS, Janela, classificar, dia_util, momento_local

LIMITE_MENSAL_PADRAO = 20_000
MARGEM_DE_SEGURANCA = 0.15
DIAS_CORRIDOS_NO_MES = 31
DIAS_UTEIS_NO_MES = 23


def duracao_minutos(janela: Janela) -> int:
    for faixa, inicio, fim in FAIXAS:
        if faixa is janela:
            minutos_inicio = inicio.hour * 60 + inicio.minute
            minutos_fim = fim.hour * 60 + fim.minute
            return minutos_fim - minutos_inicio
    raise ValueError(f"janela desconhecida: {janela}")


class Cadencia(BaseModel):
    model_config = ConfigDict(frozen=True)

    intervalos_min: dict[Janela, int] = Field(default_factory=dict)
    apenas_dias_uteis: bool = False

    def intervalo(self, janela: Janela) -> int | None:
        return self.intervalos_min.get(janela)

    def coletas_por_dia(self) -> int:
        total = 0
        for janela, intervalo in self.intervalos_min.items():
            if intervalo <= 0:
                continue
            total += duracao_minutos(janela) // intervalo
        return total

    def dias_por_mes(self) -> int:
        return DIAS_UTEIS_NO_MES if self.apenas_dias_uteis else DIAS_CORRIDOS_NO_MES

    def coletas_por_mes(self) -> int:
        return self.coletas_por_dia() * self.dias_por_mes()

    def deve_coletar(self, momento: datetime) -> bool:
        if self.apenas_dias_uteis and not dia_util(momento):
            return False
        intervalo = self.intervalo(classificar(momento))
        if intervalo is None or intervalo <= 0:
            return False
        local = momento_local(momento)
        return local.minute % intervalo < self.tolerancia_min

    @property
    def tolerancia_min(self) -> int:
        return 5


class ConsumoDoLote(BaseModel):
    model_config = ConfigDict(frozen=True)

    lote: str
    segmentos: int
    coletas_por_dia: int
    requisicoes_por_mes: int


class Orcamento(BaseModel):
    model_config = ConfigDict(frozen=True)

    limite_mensal: int = LIMITE_MENSAL_PADRAO
    margem: float = MARGEM_DE_SEGURANCA
    consumos: tuple[ConsumoDoLote, ...] = ()

    @property
    def teto_utilizavel(self) -> int:
        return int(self.limite_mensal * (1 - self.margem))

    @property
    def requisicoes_por_mes(self) -> int:
        return sum(consumo.requisicoes_por_mes for consumo in self.consumos)

    @property
    def folga(self) -> int:
        return self.teto_utilizavel - self.requisicoes_por_mes

    @property
    def uso_do_limite(self) -> float:
        return self.requisicoes_por_mes / self.limite_mensal

    @property
    def cabe(self) -> bool:
        return self.folga >= 0

    def vida_restante(self, requisicoes_gastas: int) -> timedelta:
        por_dia = sum(consumo.coletas_por_dia * consumo.segmentos for consumo in self.consumos)
        if por_dia <= 0:
            return timedelta(0)
        restante = max(self.limite_mensal - requisicoes_gastas, 0)
        return timedelta(days=restante / por_dia)
