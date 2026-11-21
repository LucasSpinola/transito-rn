from __future__ import annotations

import pytest

from tests.test_analise import SEGMENTOS, semear
from transito_natal.analytics.analise import Analise
from transito_natal.reporting import tabelas
from transito_natal.reporting.relatorio import MARCA_FINAL, MARCA_INICIAL, gerar, injetar

COLUNAS = {"via": "Via", "indice_medio": "Indice medio", "chovendo": "Chovendo"}


def test_tabela_vazia_devolve_aviso():
    assert tabelas.markdown([], COLUNAS) == "Sem amostras suficientes para esta tabela."


def test_tabela_formata_decimal_com_virgula_e_booleano_em_texto():
    linhas = [{"via": "Avenida Abel Cabral", "indice_medio": 1.234, "chovendo": True}]
    gerado = tabelas.markdown(linhas, COLUNAS)
    assert "| Via | Indice medio | Chovendo |" in gerado
    assert "| Avenida Abel Cabral | 1,23 | sim |" in gerado


def test_tabela_marca_coluna_ausente():
    assert "sem dado" in tabelas.markdown([{"via": "Avenida Abel Cabral"}], COLUNAS)


@pytest.fixture
def gerado(tmp_path):
    semear(tmp_path / "dados", com_chuva=True)
    with Analise(tmp_path / "dados", SEGMENTOS) as analise:
        yield gerar(analise, SEGMENTOS, tmp_path / "docs" / "figuras", tmp_path / "achados.md")


def test_relatorio_escreve_achados_e_figuras(gerado):
    texto = gerado.achados.read_text(encoding="utf-8")
    assert "Serie de 60 amostras" in texto
    assert "Gargalos medidos" in texto
    assert "Efeito da chuva" in texto
    assert len(gerado.figuras) == 3
    assert all(figura.exists() and figura.stat().st_size > 0 for figura in gerado.figuras)


def test_relatorio_desenha_mapa_navegavel(gerado):
    assert gerado.mapa is not None
    conteudo = gerado.mapa.read_text(encoding="utf-8")
    assert "Avenida Maria Lacerda Montenegro" in conteudo
    assert "indice medio" in conteudo


def test_relatorio_sem_amostras_nao_gera_figura(tmp_path):
    with Analise(tmp_path / "vazio", SEGMENTOS) as analise:
        vazio = gerar(analise, SEGMENTOS, tmp_path / "figuras", tmp_path / "achados.md")
    assert vazio.figuras == ()
    assert vazio.mapa is None
    assert "Nenhuma amostra coletada" in vazio.achados.read_text(encoding="utf-8")


def test_injecao_substitui_apenas_o_trecho_marcado(gerado, tmp_path):
    leia_me = tmp_path / "README.md"
    leia_me.write_text(
        f"# titulo\n\ntexto antes\n\n{MARCA_INICIAL}\nconteudo velho\n{MARCA_FINAL}"
        "\n\ntexto depois\n",
        encoding="utf-8",
    )
    assert injetar(leia_me, gerado.achados)
    texto = leia_me.read_text(encoding="utf-8")
    assert "conteudo velho" not in texto
    assert "texto antes" in texto
    assert "texto depois" in texto
    assert "Gargalos medidos" in texto


def test_injecao_ignora_arquivo_sem_marcas(gerado, tmp_path):
    leia_me = tmp_path / "README.md"
    leia_me.write_text("# titulo\n", encoding="utf-8")
    assert not injetar(leia_me, gerado.achados)
    assert leia_me.read_text(encoding="utf-8") == "# titulo\n"


def test_injecao_ignora_arquivo_inexistente(gerado, tmp_path):
    assert not injetar(tmp_path / "ausente.md", gerado.achados)
