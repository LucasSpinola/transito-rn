from __future__ import annotations

import pytest

from tests.fabricas import segmento
from transito_rn.adapters.prf.importacao import ImportadorPRF, arquivos_de_entrada
from transito_rn.analytics.sinistros import AnaliseDeSinistros
from transito_rn.ports.erros import RespostaInvalida

CABECALHO = (
    "id;data_inversa;dia_semana;horario;uf;br;km;municipio;causa_acidente;"
    "tipo_acidente;"
    "classificacao_acidente;fase_dia;sentido_via;condicao_metereologica;tipo_pista;tracado_via;"
    "uso_solo;pessoas;mortos;feridos_leves;feridos_graves;ilesos;ignorados;feridos;veiculos;"
    "latitude;longitude;regional;delegacia;uop"
)

LINHAS = [
    "1;2024-03-04;Segunda;07:30:00;RN;101;123,5;PARNAMIRIM;Velocidade incompativel;"
    "Colisao traseira;"
    "Com Vitimas Fatais;Pleno dia;Crescente;Ceu Claro;Dupla;Reta;Urbano;4;2;1;1;0;0;2;2;"
    "-5,8738897;-35,2209179;SPRF-RN;DEL01;UOP01",
    "2;2024-03-05;Terca;19:10:00;RN;101;127,0;PARNAMIRIM;Falta de atencao;Colisao lateral;"
    "Com Vitimas Feridas;Plena noite;Decrescente;Chuva;Dupla;Curva;Urbano;3;0;2;1;0;0;3;2;"
    "-5,8700000;-35,2200000;SPRF-RN;DEL01;UOP01",
    "3;2025-06-10;Terca;12:00:00;RN;304;60,2;ASSU;Ingestao de alcool;Saida de pista;"
    "Com Vitimas Fatais;Pleno dia;Crescente;Ceu Claro;Simples;Reta;Rural;2;1;0;1;1;0;1;1;"
    "-5,6002791;-36,9244041;SPRF-RN;DEL02;UOP02",
    "4;2025-06-11;Quarta;03:00:00;PB;101;10,0;JOAO PESSOA;Falta de atencao;Colisao frontal;"
    "Com Vitimas Fatais;Plena noite;Crescente;Ceu Claro;Simples;Reta;Rural;2;2;0;0;0;0;0;2;"
    "-7,1000000;-34,8000000;SPRF-PB;DEL03;UOP03",
]


@pytest.fixture
def origem(tmp_path):
    pasta = tmp_path / "externo" / "prf"
    pasta.mkdir(parents=True)
    (pasta / "acidentes2024.csv").write_text(
        "\n".join([CABECALHO, LINHAS[0], LINHAS[1]]), encoding="latin-1"
    )
    (pasta / "acidentes2025.csv").write_text(
        "\n".join([CABECALHO, LINHAS[2], LINHAS[3]]), encoding="latin-1"
    )
    return pasta


@pytest.fixture
def analise(origem, tmp_path):
    with ImportadorPRF() as importador:
        importador.importar(origem, tmp_path / "dados")
    with AnaliseDeSinistros(tmp_path / "dados", (segmento("mlm-cei"),)) as instancia:
        yield instancia


def test_sem_arquivo_a_importacao_falha_com_mensagem_util(tmp_path):
    with pytest.raises(RespostaInvalida, match="nenhum csv da prf"), ImportadorPRF() as importador:
        importador.importar(tmp_path / "vazio", tmp_path / "dados")


def test_arquivo_fora_do_formato_da_prf_e_recusado(tmp_path):
    pasta = tmp_path / "prf"
    pasta.mkdir()
    (pasta / "qualquer.csv").write_text("a;b;c\n1;2;3\n", encoding="latin-1")
    with (
        pytest.raises(RespostaInvalida, match="nao parece ser um csv da prf"),
        ImportadorPRF() as (importador),
    ):
        importador.importar(pasta, tmp_path / "dados")


def test_localiza_os_csv_em_subpastas(origem):
    assert len(arquivos_de_entrada(origem)) == 2


def test_importacao_filtra_a_unidade_da_federacao(origem, tmp_path):
    with ImportadorPRF() as importador:
        resultado = importador.importar(origem, tmp_path / "dados")
    assert resultado.arquivos == 2
    assert resultado.linhas_lidas == 4
    assert resultado.linhas_da_uf == 3
    assert (resultado.primeiro_ano, resultado.ultimo_ano) == (2024, 2025)


def test_base_vazia_nao_quebra_as_consultas(tmp_path):
    with AnaliseDeSinistros(tmp_path / "nada") as instancia:
        assert instancia.vazio
        assert instancia.trechos_mais_letais() == []
        assert instancia.cobertura()["ocorrencias"] == 0


def test_cobertura_soma_vitimas(analise):
    cobertura = analise.cobertura()
    assert cobertura["ocorrencias"] == 3
    assert cobertura["mortos"] == 3
    assert cobertura["feridos_graves"] == 3


def test_quilometro_com_virgula_vira_numero(analise):
    trechos = analise.trechos_mais_letais()
    faixas = {(linha["br"], linha["km_inicial"], linha["km_final"]) for linha in trechos}
    assert ("101", 120, 130) in faixas
    assert ("304", 60, 70) in faixas


def test_trechos_ordenam_por_mortes(analise):
    trechos = analise.trechos_mais_letais()
    assert trechos[0]["mortos"] >= trechos[-1]["mortos"]
    assert trechos[0]["br"] == "101"


def test_filtro_por_ano_reduz_a_amostra(analise):
    assert len(analise.trechos_mais_letais(desde=2025)) == 1
    assert len(analise.trechos_mais_letais()) == 2


def test_ranking_por_municipio_ignora_outras_unidades(analise):
    municipios = {linha["municipio"] for linha in analise.por_municipio()}
    assert municipios == {"PARNAMIRIM", "ASSU"}


def test_causas_vem_ordenadas_por_ocorrencia(analise):
    causas = analise.por_causa()
    assert len(causas) == 3
    assert causas[0]["ocorrencias"] >= causas[-1]["ocorrencias"]


def test_perfil_por_fase_do_dia_calcula_letalidade(analise):
    perfil = {linha["fase_dia"]: linha for linha in analise.perfil_horario()}
    assert perfil["Pleno dia"]["ocorrencias"] == 2
    assert perfil["Pleno dia"]["letalidade"] == pytest.approx(150.0)


def test_cruzamento_conta_sinistros_perto_do_segmento(analise):
    ao_redor = {linha["segmento"]: linha for linha in analise.ao_redor_dos_segmentos(raio_km=5)}
    assert ao_redor["mlm-cei"]["ocorrencias"] == 2


def test_raio_menor_reduz_a_contagem(analise):
    estreito = analise.ao_redor_dos_segmentos(raio_km=0.5)[0]
    assert estreito["ocorrencias"] < 2


def test_serie_anual_cobre_os_dois_anos(analise):
    anos = [linha["ano"] for linha in analise.por_ano()]
    assert anos == [2024, 2025]
