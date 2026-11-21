from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ClasseVia(StrEnum):
    TRONCAL = "troncal"
    ARTERIAL = "arterial"
    COLETORA = "coletora"
    LOCAL = "local"


class Coordenada(BaseModel):
    model_config = ConfigDict(frozen=True)

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class Segmento(BaseModel):
    model_config = ConfigDict(frozen=True)

    identificador: str
    via: str
    referencia: str
    bairro: str
    municipio: str
    classe: ClasseVia
    ponto: Coordenada
    lote: str
    zoom: int = Field(default=15, ge=0, le=22)
    sentido: str | None = None
    frc_esperado: str | None = None
    motivo: str | None = None


class AmostraTrafego(BaseModel):
    model_config = ConfigDict(frozen=True)

    segmento: str
    lote: str = ""
    coletado_em: datetime
    velocidade_atual_kmh: float = Field(ge=0)
    velocidade_livre_kmh: float = Field(gt=0)
    tempo_atual_s: float = Field(gt=0)
    tempo_livre_s: float = Field(gt=0)
    comprimento_m: float = Field(gt=0)
    confianca: float = Field(ge=0, le=1)
    via_fechada: bool = False
    frc: str | None = None


class AmostraClima(BaseModel):
    model_config = ConfigDict(frozen=True)

    coletado_em: datetime
    chuva_mm: float = Field(ge=0)
    temperatura_c: float
    vento_kmh: float = Field(ge=0)
