from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import duckdb

from transito_rn.adapters.prf.importacao import PASTA_SINISTROS
from transito_rn.domain.modelos import Segmento

Registro = dict[str, Any]

FAIXA_KM = 10
RAIO_PADRAO_KM = 5.0
RAIO_DA_TERRA_KM = 6371.0


class AnaliseDeSinistros:
    def __init__(self, raiz: Path, segmentos: Sequence[Segmento] = ()) -> None:
        self.raiz = raiz
        self.conexao = duckdb.connect(":memory:")
        self._registrar(segmentos)

    def __enter__(self) -> AnaliseDeSinistros:
        return self

    def __exit__(self, *_: object) -> None:
        self.conexao.close()

    @property
    def vazio(self) -> bool:
        return self.conexao.execute("SELECT count(*) FROM sinistros").fetchone()[0] == 0

    def cobertura(self) -> Registro:
        return self._um(
            """
            SELECT
                count(*) AS ocorrencias,
                sum(mortos) AS mortos,
                sum(feridos_graves) AS feridos_graves,
                min(ano) AS primeiro_ano,
                max(ano) AS ultimo_ano
            FROM sinistros
            """
        )

    def por_ano(self) -> list[Registro]:
        return self._varios(
            """
            SELECT ano, count(*) AS ocorrencias, sum(mortos) AS mortos
            FROM sinistros
            GROUP BY ALL
            ORDER BY ano
            """
        )

    def trechos_mais_letais(self, limite: int = 15, desde: int | None = None) -> list[Registro]:
        return self._varios(
            f"""
            SELECT
                br,
                (floor(km / {FAIXA_KM}) * {FAIXA_KM})::INTEGER AS km_inicial,
                (floor(km / {FAIXA_KM}) * {FAIXA_KM} + {FAIXA_KM})::INTEGER AS km_final,
                any_value(municipio) AS municipio_de_referencia,
                count(*) AS ocorrencias,
                sum(mortos) AS mortos,
                sum(feridos_graves) AS feridos_graves,
                round(avg(latitude), 5) AS latitude,
                round(avg(longitude), 5) AS longitude
            FROM sinistros
            WHERE br IS NOT NULL AND km IS NOT NULL AND (? IS NULL OR ano >= ?)
            GROUP BY ALL
            ORDER BY mortos DESC, ocorrencias DESC, br, km_inicial
            LIMIT ?
            """,
            [desde, desde, limite],
        )

    def por_municipio(self, limite: int = 15, desde: int | None = None) -> list[Registro]:
        return self._varios(
            """
            SELECT
                municipio,
                count(*) AS ocorrencias,
                sum(mortos) AS mortos,
                sum(feridos_graves) AS feridos_graves
            FROM sinistros
            WHERE municipio IS NOT NULL AND (? IS NULL OR ano >= ?)
            GROUP BY ALL
            ORDER BY mortos DESC, ocorrencias DESC, municipio
            LIMIT ?
            """,
            [desde, desde, limite],
        )

    def por_causa(self, limite: int = 10, desde: int | None = None) -> list[Registro]:
        return self._varios(
            """
            SELECT
                causa_acidente AS causa,
                count(*) AS ocorrencias,
                sum(mortos) AS mortos
            FROM sinistros
            WHERE causa_acidente IS NOT NULL AND (? IS NULL OR ano >= ?)
            GROUP BY ALL
            ORDER BY ocorrencias DESC, causa
            LIMIT ?
            """,
            [desde, desde, limite],
        )

    def perfil_horario(self, desde: int | None = None) -> list[Registro]:
        return self._varios(
            """
            SELECT
                fase_dia,
                count(*) AS ocorrencias,
                sum(mortos) AS mortos,
                round(100.0 * sum(mortos) / count(*), 2) AS letalidade
            FROM sinistros
            WHERE fase_dia IS NOT NULL AND (? IS NULL OR ano >= ?)
            GROUP BY ALL
            ORDER BY ocorrencias DESC
            """,
            [desde, desde],
        )

    def ao_redor_dos_segmentos(
        self, raio_km: float = RAIO_PADRAO_KM, desde: int | None = None
    ) -> list[Registro]:
        return self._varios(
            f"""
            SELECT
                s.identificador AS segmento,
                s.via,
                s.municipio,
                count(a.data) AS ocorrencias,
                coalesce(sum(a.mortos), 0) AS mortos,
                coalesce(sum(a.feridos_graves), 0) AS feridos_graves
            FROM segmentos s
            LEFT JOIN sinistros a
                ON a.latitude IS NOT NULL
                AND a.longitude IS NOT NULL
                AND (? IS NULL OR a.ano >= ?)
                AND {RAIO_DA_TERRA_KM} * 2 * asin(sqrt(
                    pow(sin(radians(a.latitude - s.latitude) / 2), 2)
                    + cos(radians(s.latitude)) * cos(radians(a.latitude))
                    * pow(sin(radians(a.longitude - s.longitude) / 2), 2)
                )) <= ?
            GROUP BY ALL
            ORDER BY mortos DESC, ocorrencias DESC, segmento
            """,
            [desde, desde, raio_km],
        )

    def _registrar(self, segmentos: Sequence[Segmento]) -> None:
        arquivos = list((self.raiz / PASTA_SINISTROS).glob("*.parquet"))
        if arquivos:
            padrao = str(self.raiz / PASTA_SINISTROS / "*.parquet").replace("'", "''")
            self.conexao.execute(
                "CREATE VIEW sinistros AS "
                f"SELECT * FROM read_parquet('{padrao}', union_by_name = true)"
            )
        else:
            self.conexao.execute(
                """
                CREATE TABLE sinistros (
                    data DATE, ano INTEGER, uf TEXT, br TEXT, km DOUBLE,
                    latitude DOUBLE, longitude DOUBLE,
                    mortos INTEGER, feridos_leves INTEGER, feridos_graves INTEGER,
                    ilesos INTEGER, pessoas INTEGER, veiculos INTEGER,
                    municipio TEXT, causa_acidente TEXT, tipo_acidente TEXT,
                    classificacao_acidente TEXT, fase_dia TEXT,
                    condicao_metereologica TEXT, tipo_pista TEXT,
                    tracado_via TEXT, dia_semana TEXT
                )
                """
            )
        self.conexao.execute(
            "CREATE TABLE segmentos (identificador TEXT, via TEXT, municipio TEXT, "
            "latitude DOUBLE, longitude DOUBLE)"
        )
        if segmentos:
            self.conexao.executemany(
                "INSERT INTO segmentos VALUES (?, ?, ?, ?, ?)",
                [
                    (
                        segmento.identificador,
                        segmento.via,
                        segmento.municipio,
                        segmento.ponto.latitude,
                        segmento.ponto.longitude,
                    )
                    for segmento in segmentos
                ],
            )

    def _varios(self, consulta: str, parametros: Sequence[Any] | None = None) -> list[Registro]:
        resultado = self.conexao.execute(consulta, list(parametros or []))
        colunas = [descricao[0] for descricao in resultado.description]
        return [dict(zip(colunas, linha, strict=True)) for linha in resultado.fetchall()]

    def _um(self, consulta: str, parametros: Sequence[Any] | None = None) -> Registro:
        registros = self._varios(consulta, parametros)
        return registros[0] if registros else {}
