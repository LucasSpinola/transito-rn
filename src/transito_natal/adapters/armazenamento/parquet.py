from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from transito_natal.adapters.armazenamento.esquemas import CLIMA, TRAFEGO
from transito_natal.domain.modelos import AmostraClima, AmostraTrafego

PASTA_TRAFEGO = "trafego"
PASTA_CLIMA = "clima"


def particao(momento: datetime) -> str:
    return f"dt={momento.date().isoformat()}"


def nome_do_arquivo(momento: datetime) -> str:
    return f"{momento.strftime('%H%M%S')}.parquet"


class RepositorioParquet:
    def __init__(self, raiz: Path) -> None:
        self.raiz = raiz

    def gravar(self, amostras: Sequence[AmostraTrafego]) -> int:
        if not amostras:
            return 0
        registros = [amostra.model_dump() for amostra in amostras]
        return self._escrever(PASTA_TRAFEGO, TRAFEGO, registros, amostras[0].coletado_em)

    def gravar_clima(self, amostras: Sequence[AmostraClima]) -> int:
        if not amostras:
            return 0
        registros = [amostra.model_dump() for amostra in amostras]
        return self._escrever(PASTA_CLIMA, CLIMA, registros, amostras[0].coletado_em)

    def dias_disponiveis(self) -> Sequence[date]:
        pasta = self.raiz / PASTA_TRAFEGO
        if not pasta.exists():
            return ()
        dias = [
            date.fromisoformat(filho.name.removeprefix("dt="))
            for filho in sorted(pasta.iterdir())
            if filho.is_dir() and filho.name.startswith("dt=")
        ]
        return tuple(dias)

    def total_de_amostras(self) -> int:
        pasta = self.raiz / PASTA_TRAFEGO
        if not pasta.exists():
            return 0
        return sum(
            pq.ParquetFile(arquivo).metadata.num_rows for arquivo in pasta.rglob("*.parquet")
        )

    def _escrever(
        self,
        conjunto: str,
        esquema: pa.Schema,
        registros: list[dict[str, object]],
        momento: datetime,
    ) -> int:
        destino = self.raiz / conjunto / particao(momento)
        destino.mkdir(parents=True, exist_ok=True)
        tabela = pa.Table.from_pylist(registros, schema=esquema)
        pq.write_table(tabela, destino / nome_do_arquivo(momento), compression="zstd")
        return tabela.num_rows
