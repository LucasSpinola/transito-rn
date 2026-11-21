from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

import duckdb

from transito_rn.ports.erros import RespostaInvalida

UF_PADRAO = "RN"
PASTA_SINISTROS = "sinistros"

COLUNAS_EXIGIDAS = (
    "data_inversa",
    "uf",
    "br",
    "km",
    "municipio",
    "causa_acidente",
    "tipo_acidente",
    "classificacao_acidente",
    "mortos",
)

NUMERICAS_COM_VIRGULA = ("km", "latitude", "longitude")
INTEIRAS = ("mortos", "feridos_leves", "feridos_graves", "ilesos", "pessoas", "veiculos")
TEXTUAIS = (
    "municipio",
    "causa_acidente",
    "tipo_acidente",
    "classificacao_acidente",
    "fase_dia",
    "condicao_metereologica",
    "tipo_pista",
    "tracado_via",
    "dia_semana",
)


class ResultadoDaImportacao(NamedTuple):
    arquivos: int
    linhas_lidas: int
    linhas_da_uf: int
    destino: Path
    primeiro_ano: int | None
    ultimo_ano: int | None


def _numero(coluna: str, disponiveis: set[str]) -> str:
    if coluna not in disponiveis:
        return f"NULL AS {coluna}"
    return f"try_cast(replace(trim({coluna}), ',', '.') AS DOUBLE) AS {coluna}"


def _inteiro(coluna: str, disponiveis: set[str]) -> str:
    if coluna not in disponiveis:
        return f"NULL AS {coluna}"
    return f"coalesce(try_cast(trim({coluna}) AS INTEGER), 0) AS {coluna}"


def _texto(coluna: str, disponiveis: set[str]) -> str:
    if coluna not in disponiveis:
        return f"NULL AS {coluna}"
    return f"nullif(trim({coluna}), '') AS {coluna}"


def arquivos_de_entrada(origem: Path) -> Sequence[Path]:
    if not origem.exists():
        return ()
    return tuple(sorted(caminho for caminho in origem.rglob("*.csv")))


class ImportadorPRF:
    def __init__(self, uf: str = UF_PADRAO) -> None:
        self.uf = uf
        self.conexao = duckdb.connect(":memory:")

    def __enter__(self) -> ImportadorPRF:
        return self

    def __exit__(self, *_: object) -> None:
        self.conexao.close()

    def importar(self, origem: Path, destino: Path) -> ResultadoDaImportacao:
        arquivos = arquivos_de_entrada(origem)
        if not arquivos:
            raise RespostaInvalida(f"nenhum csv da prf encontrado em {origem}")

        lidas = 0
        for arquivo in arquivos:
            lidas += self._carregar(arquivo)

        pasta = destino / PASTA_SINISTROS
        pasta.mkdir(parents=True, exist_ok=True)
        self.conexao.execute(
            "COPY (SELECT * FROM sinistros ORDER BY data) TO ? (FORMAT parquet, COMPRESSION zstd)",
            [str(pasta / f"{self.uf.lower()}.parquet")],
        )
        total, primeiro, ultimo = self.conexao.execute(
            "SELECT count(*), min(ano), max(ano) FROM sinistros"
        ).fetchone()
        return ResultadoDaImportacao(
            arquivos=len(arquivos),
            linhas_lidas=lidas,
            linhas_da_uf=total,
            destino=pasta,
            primeiro_ano=primeiro,
            ultimo_ano=ultimo,
        )

    def _carregar(self, arquivo: Path) -> int:
        leitura = (
            "read_csv(?, delim=';', header=true, encoding='latin-1', "
            "all_varchar=true, ignore_errors=true, null_padding=true)"
        )
        colunas = self.conexao.execute(
            f"SELECT * FROM {leitura} LIMIT 0", [str(arquivo)]
        ).description
        disponiveis = {nome.lower() for nome, *_ in colunas}

        faltantes = [coluna for coluna in COLUNAS_EXIGIDAS if coluna not in disponiveis]
        if faltantes:
            raise RespostaInvalida(
                f"{arquivo.name} nao parece ser um csv da prf, faltam: {', '.join(faltantes)}"
            )

        projecao = ", ".join(
            [
                "try_cast(data_inversa AS DATE) AS data",
                "extract('year' FROM try_cast(data_inversa AS DATE))::INTEGER AS ano",
                "upper(trim(uf)) AS uf",
                "nullif(trim(br), '') AS br",
                *[_numero(coluna, disponiveis) for coluna in NUMERICAS_COM_VIRGULA],
                *[_inteiro(coluna, disponiveis) for coluna in INTEIRAS],
                *[_texto(coluna, disponiveis) for coluna in TEXTUAIS],
            ]
        )
        consulta = f"SELECT {projecao} FROM {leitura} WHERE upper(trim(uf)) = ?"
        if self._tem("sinistros"):
            self.conexao.execute(
                f"INSERT INTO sinistros BY NAME {consulta}", [str(arquivo), self.uf]
            )
        else:
            self.conexao.execute(f"CREATE TABLE sinistros AS {consulta}", [str(arquivo), self.uf])
        return self.conexao.execute(f"SELECT count(*) FROM {leitura}", [str(arquivo)]).fetchone()[0]

    def _tem(self, tabela: str) -> bool:
        return bool(
            self.conexao.execute(
                "SELECT count(*) FROM duckdb_tables() WHERE table_name = ?", [tabela]
            ).fetchone()[0]
        )
