from __future__ import annotations

from datetime import UTC, datetime

from transito_natal.domain.modelos import (
    AmostraTrafego,
    ClasseVia,
    Coordenada,
    Segmento,
)


def segmento(identificador: str = "mlm-cei", **ajustes: object) -> Segmento:
    dados = {
        "identificador": identificador,
        "via": "Avenida Maria Lacerda Montenegro",
        "referencia": "frente ao CEI Zona Sul",
        "bairro": "Nova Parnamirim",
        "municipio": "Parnamirim",
        "corredor": "nova-parnamirim",
        "classe": ClasseVia.ARTERIAL,
        "ponto": Coordenada(latitude=-5.8786711, longitude=-35.2165393),
    }
    dados.update(ajustes)
    return Segmento.model_validate(dados)


def amostra(
    velocidade_atual_kmh: float = 20.0,
    velocidade_livre_kmh: float = 50.0,
    comprimento_m: float = 500.0,
    coletado_em: datetime | None = None,
    **ajustes: object,
) -> AmostraTrafego:
    dados = {
        "segmento": "mlm-cei",
        "coletado_em": coletado_em or datetime(2026, 11, 20, 10, 0, tzinfo=UTC),
        "velocidade_atual_kmh": velocidade_atual_kmh,
        "velocidade_livre_kmh": velocidade_livre_kmh,
        "tempo_atual_s": comprimento_m / 1000 / velocidade_atual_kmh * 3600,
        "tempo_livre_s": comprimento_m / 1000 / velocidade_livre_kmh * 3600,
        "comprimento_m": comprimento_m,
        "confianca": 0.95,
    }
    dados.update(ajustes)
    return AmostraTrafego.model_validate(dados)
