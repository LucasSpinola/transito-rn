from __future__ import annotations

from datetime import datetime

import httpx

from transito_natal.domain.modelos import AmostraClima, Coordenada
from transito_natal.ports.erros import FonteIndisponivel, RespostaInvalida

BASE_URL = "https://api.open-meteo.com/v1/forecast"
VARIAVEIS = "precipitation,temperature_2m,wind_speed_10m"


class FonteOpenMeteo:
    def __init__(self, cliente: httpx.Client | None = None, base_url: str = BASE_URL) -> None:
        self._base_url = base_url
        self._cliente = cliente or httpx.Client(timeout=httpx.Timeout(15.0))

    def amostrar(self, ponto: Coordenada, momento: datetime) -> AmostraClima:
        parametros = {
            "latitude": ponto.latitude,
            "longitude": ponto.longitude,
            "current": VARIAVEIS,
            "timezone": "UTC",
        }
        try:
            resposta = self._cliente.get(self._base_url, params=parametros)
            resposta.raise_for_status()
        except httpx.HTTPError as erro:
            raise FonteIndisponivel("falha ao consultar o open-meteo") from erro

        atual = resposta.json().get("current")
        if not isinstance(atual, dict):
            raise RespostaInvalida("resposta do open-meteo sem bloco current")
        return AmostraClima(
            coletado_em=momento,
            chuva_mm=float(atual.get("precipitation") or 0.0),
            temperatura_c=float(atual["temperature_2m"]),
            vento_kmh=float(atual.get("wind_speed_10m") or 0.0),
        )

    def fechar(self) -> None:
        self._cliente.close()

    def __enter__(self) -> FonteOpenMeteo:
        return self

    def __exit__(self, *_: object) -> None:
        self.fechar()
