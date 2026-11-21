from __future__ import annotations

import time
from datetime import UTC, datetime

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from transito_natal.adapters.tomtom.mapeamento import para_amostra
from transito_natal.domain.modelos import AmostraTrafego, Segmento
from transito_natal.ports.erros import (
    FonteIndisponivel,
    LimiteDeRequisicoesExcedido,
)

BASE_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute"
QPS_PADRAO = 5.0
TENTATIVAS = 3


class LimitadorDeTaxa:
    def __init__(self, por_segundo: float) -> None:
        self._intervalo = 1 / por_segundo if por_segundo > 0 else 0.0
        self._ultima = 0.0

    def aguardar(self) -> None:
        if self._intervalo <= 0:
            return
        espera = self._intervalo - (time.monotonic() - self._ultima)
        if espera > 0:
            time.sleep(espera)
        self._ultima = time.monotonic()


class FonteTomTom:
    def __init__(
        self,
        chave: str,
        cliente: httpx.Client | None = None,
        qps: float = QPS_PADRAO,
        base_url: str = BASE_URL,
    ) -> None:
        if not chave:
            raise ValueError("chave da api da tomtom ausente")
        self._chave = chave
        self._base_url = base_url
        self._cliente = cliente or httpx.Client(timeout=httpx.Timeout(20.0))
        self._limitador = LimitadorDeTaxa(qps)
        self.requisicoes = 0

    def fechar(self) -> None:
        self._cliente.close()

    def __enter__(self) -> FonteTomTom:
        return self

    def __exit__(self, *_: object) -> None:
        self.fechar()

    @retry(
        retry=retry_if_exception_type(FonteIndisponivel),
        stop=stop_after_attempt(TENTATIVAS),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def amostrar(self, segmento: Segmento) -> AmostraTrafego:
        self._limitador.aguardar()
        url = f"{self._base_url}/{segmento.zoom}/json"
        parametros = {
            "point": f"{segmento.ponto.latitude},{segmento.ponto.longitude}",
            "unit": "KMPH",
            "openLr": "false",
            "key": self._chave,
        }
        self.requisicoes += 1
        try:
            resposta = self._cliente.get(url, params=parametros)
        except httpx.HTTPError as erro:
            raise FonteIndisponivel(
                f"falha de rede ao consultar {segmento.identificador}"
            ) from erro

        if resposta.status_code == httpx.codes.TOO_MANY_REQUESTS:
            raise LimiteDeRequisicoesExcedido("limite de requisicoes da tomtom atingido")
        if resposta.status_code >= httpx.codes.INTERNAL_SERVER_ERROR:
            raise FonteIndisponivel(f"tomtom respondeu {resposta.status_code}")
        resposta.raise_for_status()

        return para_amostra(resposta.json(), segmento, datetime.now(UTC))
