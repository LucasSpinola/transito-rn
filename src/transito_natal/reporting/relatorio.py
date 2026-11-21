from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import NamedTuple

from transito_natal.analytics.analise import Analise
from transito_natal.domain.modelos import Segmento
from transito_natal.reporting import figuras, mapa, tabelas

MARCA_INICIAL = "<!-- inicio dos achados -->"
MARCA_FINAL = "<!-- fim dos achados -->"
SEGMENTOS_NO_PERFIL = 5

COLUNAS_DO_RANKING = {
    "via": "Via",
    "referencia": "Trecho",
    "municipio": "Municipio",
    "indice_medio": "Indice medio",
    "indice_p95": "Indice p95",
    "atraso_medio_s_km": "Atraso s/km",
    "percentual_critico": "% critico",
    "velocidade_media_kmh": "Velocidade media",
    "amostras": "Amostras",
}

COLUNAS_DA_JANELA = {
    "janela": "Janela",
    "indice_medio": "Indice medio",
    "percentual_critico": "% critico",
    "amostras": "Amostras",
}

COLUNAS_DO_DIA = {
    "nome_do_dia": "Dia",
    "indice_medio": "Indice medio",
    "percentual_critico": "% critico",
    "amostras": "Amostras",
}

COLUNAS_DA_CHUVA = {
    "chovendo": "Chovendo",
    "indice_medio": "Indice medio",
    "percentual_critico": "% critico",
    "amostras": "Amostras",
}

COLUNAS_DOS_PIORES = {
    "segmento": "Segmento",
    "momento": "Momento",
    "nome_do_dia": "Dia",
    "indice": "Indice",
    "velocidade_atual_kmh": "Velocidade",
    "nivel": "Nivel",
}


class Relatorio(NamedTuple):
    achados: Path
    figuras: tuple[Path, ...]
    mapa: Path | None


def _cabecalho(cobertura: dict[str, object]) -> str:
    if not cobertura.get("amostras"):
        return "Nenhuma amostra coletada ate agora."
    return (
        f"Serie de {tabelas.plural(cobertura['amostras'], 'amostra', 'amostras')} em "
        f"{tabelas.plural(cobertura['segmentos'], 'segmento', 'segmentos')}, cobrindo "
        f"{tabelas.plural(cobertura['dias'], 'dia', 'dias')}, de {cobertura['primeiro_dia']} "
        f"a {cobertura['ultimo_dia']}."
    )


def _secao(titulo: str, corpo: str) -> str:
    return f"### {titulo}\n\n{corpo}\n"


def gerar(
    analise: Analise,
    segmentos: Sequence[Segmento],
    pasta_de_figuras: Path,
    destino: Path,
) -> Relatorio:
    cobertura = analise.cobertura()
    ranking = analise.ranking_de_gargalos()
    partes = [_cabecalho(cobertura), ""]
    geradas: list[Path] = []
    desenho: Path | None = None

    if ranking:
        geradas.append(figuras.ranking(ranking, pasta_de_figuras / "ranking.png"))
        partes.append("![Ranking de gargalos](docs/figuras/ranking.png)\n")
        partes.append(_secao("Gargalos medidos", tabelas.markdown(ranking, COLUNAS_DO_RANKING)))

        series = {
            linha["segmento"]: analise.perfil_por_hora(linha["segmento"])
            for linha in ranking[:SEGMENTOS_NO_PERFIL]
        }
        geradas.append(figuras.perfil_horario(series, pasta_de_figuras / "perfil-horario.png"))
        partes.append("![Perfil horario](docs/figuras/perfil-horario.png)\n")

        calor = analise.mapa_de_calor()
        if calor:
            geradas.append(figuras.mapa_de_calor(calor, pasta_de_figuras / "mapa-de-calor.png"))
            partes.append("![Mapa de calor](docs/figuras/mapa-de-calor.png)\n")

        desenho = mapa.desenhar(ranking, segmentos, pasta_de_figuras.parent / "mapa.html")

    partes.append(
        _secao(
            "Quando o transito aperta",
            tabelas.markdown(analise.perfil_por_janela(), COLUNAS_DA_JANELA),
        )
    )
    partes.append(
        _secao(
            "Por dia da semana",
            tabelas.markdown(analise.perfil_por_dia_da_semana(), COLUNAS_DO_DIA),
        )
    )
    partes.append(
        _secao("Efeito da chuva", tabelas.markdown(analise.efeito_da_chuva(), COLUNAS_DA_CHUVA))
    )
    partes.append(
        _secao(
            "Piores momentos registrados",
            tabelas.markdown(analise.piores_momentos(), COLUNAS_DOS_PIORES),
        )
    )

    corpo = "\n".join(partes).rstrip() + "\n"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(corpo, encoding="utf-8")
    return Relatorio(achados=destino, figuras=tuple(geradas), mapa=desenho)


def injetar(leia_me: Path, achados: Path) -> bool:
    if not leia_me.exists():
        return False
    texto = leia_me.read_text(encoding="utf-8")
    if MARCA_INICIAL not in texto or MARCA_FINAL not in texto:
        return False
    antes, resto = texto.split(MARCA_INICIAL, 1)
    _, depois = resto.split(MARCA_FINAL, 1)
    gerado = (
        f"{MARCA_INICIAL}\n\n"
        f"Atualizado em {datetime.now(UTC):%d/%m/%Y %H:%M} utc pelo comando "
        f"`transito relatorio`.\n\n"
        f"{achados.read_text(encoding='utf-8').rstrip()}\n\n"
        f"{MARCA_FINAL}"
    )
    leia_me.write_text(f"{antes}{gerado}{depois}", encoding="utf-8")
    return True
