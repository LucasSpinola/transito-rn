from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict

RAIZ_DO_PROJETO = Path(__file__).resolve().parents[2]
CAMINHO_PADRAO_DO_CATALOGO = RAIZ_DO_PROJETO / "config" / "segmentos.yaml"
PASTA_PADRAO_DE_DADOS = RAIZ_DO_PROJETO / "data" / "raw"
ARQUIVO_DE_AMBIENTE = RAIZ_DO_PROJETO / ".env"


def carregar_ambiente(caminho: Path = ARQUIVO_DE_AMBIENTE) -> None:
    if not caminho.exists():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        conteudo = linha.strip()
        if not conteudo or conteudo.startswith("#") or "=" not in conteudo:
            continue
        chave, valor = conteudo.split("=", 1)
        os.environ.setdefault(chave.strip(), valor.strip())


class Configuracao(BaseModel):
    model_config = ConfigDict(frozen=True)

    catalogo: Path = CAMINHO_PADRAO_DO_CATALOGO
    dados: Path = PASTA_PADRAO_DE_DADOS
    chave_tomtom: str = ""

    @classmethod
    def do_ambiente(cls, catalogo: Path | None = None, dados: Path | None = None) -> Configuracao:
        carregar_ambiente()
        return cls(
            catalogo=catalogo or CAMINHO_PADRAO_DO_CATALOGO,
            dados=dados or PASTA_PADRAO_DE_DADOS,
            chave_tomtom=os.environ.get("TOMTOM_API_KEY", ""),
        )
