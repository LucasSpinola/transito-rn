from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer

from transito_natal.adapters.armazenamento.catalogo_yaml import Catalogo, carregar
from transito_natal.adapters.armazenamento.parquet import RepositorioParquet
from transito_natal.adapters.openmeteo.cliente import FonteOpenMeteo
from transito_natal.adapters.tomtom.cliente import FonteTomTom
from transito_natal.application.coleta import ExecutarColeta
from transito_natal.configuracao import Configuracao
from transito_natal.domain.janelas import classificar, momento_local
from transito_natal.domain.metricas import indice_tempo_viagem, nivel_servico
from transito_natal.ports.erros import ErroDeColeta

app = typer.Typer(
    help="Coleta e analise de congestionamento em Natal e na conurbacao sul",
    no_args_is_help=True,
    add_completion=False,
)

OpcaoCatalogo = Annotated[Path | None, typer.Option("--catalogo", help="Caminho do catalogo")]
OpcaoLote = Annotated[str | None, typer.Option("--lote", help="Restringe a um lote")]


def _carregar(caminho: Path | None) -> tuple[Configuracao, Catalogo]:
    configuracao = Configuracao.do_ambiente(catalogo=caminho)
    return configuracao, carregar(configuracao.catalogo)


def _exigir_chave(configuracao: Configuracao) -> str:
    if not configuracao.chave_tomtom:
        typer.secho(
            "defina TOMTOM_API_KEY no arquivo .env ou no ambiente antes de coletar",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)
    return configuracao.chave_tomtom


@app.command()
def orcamento(catalogo: OpcaoCatalogo = None) -> None:
    _, catalogo_carregado = _carregar(catalogo)
    for apenas_ativos, rotulo in ((True, "lotes ativos"), (False, "todos os lotes")):
        projecao = catalogo_carregado.orcamento(apenas_ativos=apenas_ativos)
        cor = typer.colors.GREEN if projecao.cabe else typer.colors.RED
        typer.secho(
            f"\n{rotulo}: {projecao.requisicoes_por_mes} requisicoes por mes, "
            f"{projecao.uso_do_limite:.1%} do limite de {projecao.limite_mensal}",
            fg=cor,
            bold=True,
        )
        for consumo in projecao.consumos:
            typer.echo(
                f"  {consumo.lote:<20} {consumo.segmentos:>2} segmentos  "
                f"{consumo.coletas_por_dia:>3} coletas por dia  "
                f"{consumo.requisicoes_por_mes:>6} por mes"
            )
        typer.echo(f"  folga sobre o teto utilizavel: {projecao.folga} requisicoes")


@app.command()
def segmentos(catalogo: OpcaoCatalogo = None, lote: OpcaoLote = None) -> None:
    _, catalogo_carregado = _carregar(catalogo)
    lotes = [catalogo_carregado.lote(lote)] if lote else list(catalogo_carregado.lotes)
    for item in lotes:
        estado = "ativo" if item.ativo else "inativo"
        typer.secho(f"\n{item.identificador} ({estado})", bold=True)
        typer.echo(f"  {item.descricao}")
        for segmento in item.segmentos:
            typer.echo(
                f"  {segmento.identificador:<26} zoom {segmento.zoom:>2}  "
                f"{segmento.via}, {segmento.bairro}, {segmento.municipio}"
            )


@app.command()
def coletar(
    catalogo: OpcaoCatalogo = None,
    lote: OpcaoLote = None,
    forcar: Annotated[bool, typer.Option("--forcar", help="Ignora a cadencia")] = False,
) -> None:
    configuracao, catalogo_carregado = _carregar(catalogo)
    chave = _exigir_chave(configuracao)
    momento = datetime.now(UTC)

    if lote:
        alvo = catalogo_carregado.lote(lote)
        selecionados = alvo.segmentos if forcar or alvo.cadencia.deve_coletar(momento) else ()
    else:
        selecionados = (
            catalogo_carregado.listar() if forcar else catalogo_carregado.a_coletar(momento)
        )

    if not selecionados:
        typer.echo(
            f"nada a coletar em {momento_local(momento):%d/%m %H:%M} "
            f"({classificar(momento)}), fora da cadencia configurada"
        )
        raise typer.Exit(code=0)

    repositorio = RepositorioParquet(configuracao.dados)
    with FonteTomTom(chave=chave) as trafego, FonteOpenMeteo() as clima:
        resultado = ExecutarColeta(trafego, repositorio, clima).executar(selecionados, momento)

    typer.secho(
        f"{resultado.gravados} de {resultado.consultados} segmentos gravados em "
        f"{momento_local(momento):%d/%m %H:%M} ({classificar(momento)})",
        fg=typer.colors.GREEN if resultado.completa else typer.colors.YELLOW,
        bold=True,
    )
    for falha in resultado.falhas:
        typer.secho(f"  falha em {falha.segmento}: {falha.motivo}", fg=typer.colors.YELLOW)
    if resultado.interrompida_por_limite:
        typer.secho("  rodada interrompida pelo limite da api", fg=typer.colors.RED)


@app.command()
def calibrar(catalogo: OpcaoCatalogo = None, lote: OpcaoLote = None) -> None:
    configuracao, catalogo_carregado = _carregar(catalogo)
    chave = _exigir_chave(configuracao)
    alvos = catalogo_carregado.lote(lote).segmentos if lote else catalogo_carregado.listar_tudo()

    typer.secho(f"consultando {len(alvos)} segmentos, uma requisicao cada\n", bold=True)
    momento = datetime.now(UTC)
    with FonteTomTom(chave=chave) as trafego:
        for segmento in alvos:
            try:
                amostra = trafego.amostrar(segmento)
            except ErroDeColeta as erro:
                typer.secho(f"{segmento.identificador:<26} falhou: {erro}", fg=typer.colors.RED)
                continue
            divergencia = (
                " frc divergente"
                if segmento.frc_esperado and amostra.frc != segmento.frc_esperado
                else ""
            )
            typer.echo(
                f"{segmento.identificador:<26} {amostra.frc or '?':<5} "
                f"{amostra.comprimento_m / 1000:>5.2f} km  "
                f"{amostra.velocidade_atual_kmh:>3.0f} de "
                f"{amostra.velocidade_livre_kmh:>3.0f} kmh  "
                f"indice {indice_tempo_viagem(amostra):>4.2f}  "
                f"nivel {nivel_servico(amostra)}{divergencia}"
            )
    typer.echo(
        f"\nreferencia temporal: {momento_local(momento):%d/%m %H:%M} ({classificar(momento)})"
    )


@app.command()
def status(catalogo: OpcaoCatalogo = None) -> None:
    configuracao, catalogo_carregado = _carregar(catalogo)
    repositorio = RepositorioParquet(configuracao.dados)
    dias = repositorio.dias_disponiveis()
    total = repositorio.total_de_amostras()
    ativos = catalogo_carregado.listar()

    typer.secho(f"{len(ativos)} segmentos ativos em {configuracao.dados}", bold=True)
    if not dias:
        typer.echo("nenhuma amostra coletada ainda")
        raise typer.Exit(code=0)
    typer.echo(f"{total} amostras em {len(dias)} dias, de {dias[0]} a {dias[-1]}")
    projecao = catalogo_carregado.orcamento()
    typer.echo(f"vida restante da cota no mes: {projecao.vida_restante(total).days} dias")


if __name__ == "__main__":
    app()
