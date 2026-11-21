from __future__ import annotations

from collections.abc import Sequence
from typing import Any

Registro = dict[str, Any]


def plural(quantidade: int, singular: str, plural_: str) -> str:
    return f"{quantidade} {singular if quantidade == 1 else plural_}"


def _celula(valor: Any) -> str:
    if valor is None:
        return "sem dado"
    if isinstance(valor, bool):
        return "sim" if valor else "não"
    if isinstance(valor, float):
        return f"{valor:.2f}".rstrip("0").rstrip(".").replace(".", ",") or "0"
    return str(valor)


def markdown(
    linhas: Sequence[Registro],
    colunas: dict[str, str],
    vazio: str = "Sem amostras suficientes para esta tabela.",
) -> str:
    if not linhas:
        return vazio
    cabecalho = "| " + " | ".join(colunas.values()) + " |"
    divisoria = "| " + " | ".join("---" for _ in colunas) + " |"
    corpo = [
        "| " + " | ".join(_celula(linha.get(chave)) for chave in colunas) + " |" for linha in linhas
    ]
    return "\n".join([cabecalho, divisoria, *corpo])
