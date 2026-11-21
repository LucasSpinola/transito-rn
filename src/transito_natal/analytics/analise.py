from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa

from transito_natal.adapters.armazenamento import esquemas
from transito_natal.domain.janelas import FAIXAS, FUSO_LOCAL
from transito_natal.domain.metricas import LIMIAR_CONGESTIONAMENTO, LIMIARES_NIVEL_SERVICO
from transito_natal.domain.modelos import Segmento

Registro = dict[str, Any]

TIPOS_SQL = {
    pa.string(): "TEXT",
    pa.float64(): "DOUBLE",
    pa.bool_(): "BOOLEAN",
}


def _para_sql(esquema: pa.Schema) -> tuple[tuple[str, str], ...]:
    def tipo(campo: pa.Field) -> str:
        if pa.types.is_timestamp(campo.type):
            return "TIMESTAMPTZ"
        return TIPOS_SQL[campo.type]

    return tuple((campo.name, tipo(campo)) for campo in esquema)


TRAFEGO = _para_sql(esquemas.TRAFEGO)
CLIMA = _para_sql(esquemas.CLIMA)


def _caso_de_janela(coluna: str) -> str:
    ramos = [
        f"WHEN {coluna} >= TIME '{inicio.isoformat()}' "
        f"AND {coluna} < TIME '{fim.isoformat()}' THEN '{janela}'"
        for janela, inicio, fim in FAIXAS
    ]
    return "CASE " + " ".join(ramos) + " ELSE 'noite' END"


def _caso_de_nivel(coluna: str) -> str:
    ramos = [
        f"WHEN {coluna} >= {limiar} THEN '{rotulo}'" for limiar, rotulo in LIMIARES_NIVEL_SERVICO
    ]
    return "CASE " + " ".join(ramos) + " ELSE 'F' END"


class Analise:
    def __init__(self, raiz: Path, segmentos: Sequence[Segmento]) -> None:
        self.raiz = raiz
        self.conexao = duckdb.connect(":memory:")
        self.conexao.execute("SET TimeZone = ?", [str(FUSO_LOCAL)])
        self._registrar_segmentos(segmentos)
        self._registrar_amostras()

    def __enter__(self) -> Analise:
        return self

    def __exit__(self, *_: object) -> None:
        self.conexao.close()

    @property
    def vazio(self) -> bool:
        return self.conexao.execute("SELECT count(*) FROM amostras").fetchone()[0] == 0

    def cobertura(self) -> Registro:
        return self._um(
            """
            SELECT
                count(*) AS amostras,
                count(DISTINCT segmento) AS segmentos,
                count(DISTINCT dia) AS dias,
                min(dia) AS primeiro_dia,
                max(dia) AS ultimo_dia
            FROM amostras
            """
        )

    def ranking_de_gargalos(self, minimo_de_amostras: int = 1) -> list[Registro]:
        return self._varios(
            """
            SELECT
                a.segmento,
                s.via,
                s.referencia,
                s.bairro,
                s.municipio,
                count(*) AS amostras,
                round(avg(a.indice), 3) AS indice_medio,
                round(quantile_cont(a.indice, 0.95), 3) AS indice_p95,
                round(avg(a.atraso_s_por_km), 1) AS atraso_medio_s_km,
                round(100.0 * sum(a.critica) / count(*), 1) AS percentual_critico,
                round(avg(a.velocidade_atual_kmh), 1) AS velocidade_media_kmh,
                round(max(a.velocidade_livre_kmh), 1) AS velocidade_livre_kmh
            FROM amostras a
            JOIN segmentos s ON s.identificador = a.segmento
            GROUP BY ALL
            HAVING count(*) >= ?
            ORDER BY indice_medio DESC, atraso_medio_s_km DESC, a.segmento
            """,
            [minimo_de_amostras],
        )

    def perfil_por_janela(self) -> list[Registro]:
        return self._varios(
            """
            SELECT
                janela,
                count(*) AS amostras,
                round(avg(indice), 3) AS indice_medio,
                round(100.0 * sum(critica) / count(*), 1) AS percentual_critico
            FROM amostras
            GROUP BY ALL
            ORDER BY indice_medio DESC, janela
            """
        )

    def perfil_por_hora(self, segmento: str | None = None) -> list[Registro]:
        return self._varios(
            """
            SELECT
                hora,
                count(*) AS amostras,
                round(avg(indice), 3) AS indice_medio,
                round(avg(velocidade_atual_kmh), 1) AS velocidade_media_kmh
            FROM amostras
            WHERE ? IS NULL OR segmento = ?
            GROUP BY ALL
            ORDER BY hora
            """,
            [segmento, segmento],
        )

    def perfil_por_dia_da_semana(self) -> list[Registro]:
        return self._varios(
            """
            SELECT
                dia_da_semana,
                nome_do_dia,
                count(*) AS amostras,
                round(avg(indice), 3) AS indice_medio,
                round(100.0 * sum(critica) / count(*), 1) AS percentual_critico
            FROM amostras
            GROUP BY ALL
            ORDER BY dia_da_semana
            """
        )

    def mapa_de_calor(self) -> list[Registro]:
        return self._varios(
            """
            SELECT
                segmento,
                hora,
                round(avg(indice), 3) AS indice_medio
            FROM amostras
            GROUP BY ALL
            ORDER BY segmento, hora
            """
        )

    def efeito_da_chuva(self, limiar_mm: float = 0.2) -> list[Registro]:
        return self._varios(
            """
            WITH pareado AS (
                SELECT
                    a.indice,
                    a.critica,
                    coalesce(c.chuva_mm, 0) >= ? AS chovendo
                FROM amostras a
                LEFT JOIN clima c
                    ON date_trunc('hour', a.coletado_em) = date_trunc('hour', c.coletado_em)
            )
            SELECT
                chovendo,
                count(*) AS amostras,
                round(avg(indice), 3) AS indice_medio,
                round(100.0 * sum(critica) / count(*), 1) AS percentual_critico
            FROM pareado
            GROUP BY ALL
            ORDER BY chovendo
            """,
            [limiar_mm],
        )

    def piores_momentos(self, limite: int = 10) -> list[Registro]:
        return self._varios(
            """
            SELECT
                segmento,
                strftime(local, '%d/%m %H:%M') AS momento,
                nome_do_dia,
                round(indice, 2) AS indice,
                velocidade_atual_kmh,
                nivel
            FROM amostras
            ORDER BY indice DESC, segmento, coletado_em
            LIMIT ?
            """,
            [limite],
        )

    def _registrar_segmentos(self, segmentos: Sequence[Segmento]) -> None:
        registros = [
            (
                segmento.identificador,
                segmento.via,
                segmento.referencia,
                segmento.bairro,
                segmento.municipio,
                segmento.lote,
                str(segmento.classe),
                segmento.ponto.latitude,
                segmento.ponto.longitude,
                segmento.motivo,
            )
            for segmento in segmentos
        ]
        self.conexao.execute(
            """
            CREATE TABLE segmentos (
                identificador TEXT,
                via TEXT,
                referencia TEXT,
                bairro TEXT,
                municipio TEXT,
                lote TEXT,
                classe TEXT,
                latitude DOUBLE,
                longitude DOUBLE,
                motivo TEXT
            )
            """
        )
        self.conexao.executemany(
            "INSERT INTO segmentos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", registros
        )

    def _registrar_amostras(self) -> None:
        self._carregar_conjunto("trafego", TRAFEGO)
        self._carregar_conjunto("clima", CLIMA)
        self.conexao.execute(
            f"""
            CREATE VIEW amostras AS
            WITH bruto AS (
                SELECT *, coletado_em AT TIME ZONE '{FUSO_LOCAL}' AS local
                FROM trafego_bruto
            )
            SELECT
                segmento,
                coletado_em,
                local,
                local::DATE AS dia,
                extract('hour' FROM local)::INTEGER AS hora,
                local::TIME AS horario,
                isodow(local) AS dia_da_semana,
                strftime(local, '%A') AS nome_do_dia,
                {_caso_de_janela("local::TIME")} AS janela,
                velocidade_atual_kmh,
                velocidade_livre_kmh,
                comprimento_m,
                confianca,
                via_fechada,
                frc,
                tempo_atual_s / tempo_livre_s AS indice,
                velocidade_atual_kmh / velocidade_livre_kmh AS razao,
                greatest(tempo_atual_s - tempo_livre_s, 0)
                    / (comprimento_m / 1000) AS atraso_s_por_km,
                {_caso_de_nivel("velocidade_atual_kmh / velocidade_livre_kmh")} AS nivel,
                CASE
                    WHEN via_fechada OR tempo_atual_s / tempo_livre_s >= {LIMIAR_CONGESTIONAMENTO}
                    THEN 1 ELSE 0
                END AS critica
            FROM bruto
            """
        )
        self.conexao.execute("CREATE VIEW clima AS SELECT * FROM clima_bruto")

    def _carregar_conjunto(self, conjunto: str, esquema: Sequence[tuple[str, str]]) -> None:
        colunas = ", ".join(f"{nome} {tipo}" for nome, tipo in esquema)
        self.conexao.execute(f"CREATE TABLE {conjunto}_bruto ({colunas})")
        pasta = self.raiz / conjunto
        if not pasta.exists() or not any(pasta.rglob("*.parquet")):
            return
        nomes = ", ".join(nome for nome, _ in esquema)
        self.conexao.execute(
            f"INSERT INTO {conjunto}_bruto "
            f"SELECT {nomes} FROM read_parquet(?, union_by_name = true)",
            [str(pasta / "**" / "*.parquet")],
        )

    def _varios(self, consulta: str, parametros: Sequence[Any] | None = None) -> list[Registro]:
        resultado = self.conexao.execute(consulta, list(parametros or []))
        colunas = [descricao[0] for descricao in resultado.description]
        return [dict(zip(colunas, linha, strict=True)) for linha in resultado.fetchall()]

    def _um(self, consulta: str, parametros: Sequence[Any] | None = None) -> Registro:
        registros = self._varios(consulta, parametros)
        return registros[0] if registros else {}
