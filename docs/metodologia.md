# Metodologia

## Por que o projeto gera o proprio dado

Natal nao publica serie aberta de congestionamento. O portal de dados abertos da mobilidade
([dadosabertos.natal.br](http://dadosabertos.natal.br/)) entrega o catalogo estatico de linhas,
terminais e itinerarios, e a API dinamica exige cadastro previo de desenvolvedor. O anuario
estatistico de sinistros mais recente publicado pela STTU na
[pagina de publicacoes](https://natal.rn.gov.br/sttu/publicacoes) e de 2018, e os numeros de 2024
e 2025 circulam apenas pela imprensa citando a secretaria. Os enderecos `dados.natal.br` e
`dados.sttu.natal.br` nao respondiam quando este projeto foi montado.

Sinistro tambem nao e congestionamento. Um bairro pode liderar o ranking de acidentes e ter
fluxo livre, enquanto outro trava todo dia sem registrar ocorrencia. Como nenhuma base publica
mede tempo de viagem em Natal, o repositorio constroi a sua.

## Fonte primaria

A coleta usa o endpoint [Flow Segment Data](https://docs.tomtom.com/traffic-api/documentation/traffic-flow/flow-segment-data)
da TomTom, que devolve, para um ponto geografico, o segmento viario correspondente com:

| Campo | Significado |
| --- | --- |
| `currentSpeed` | velocidade media observada agora no segmento |
| `freeFlowSpeed` | velocidade esperada em condicao ideal, sem transito |
| `currentTravelTime` | tempo de percurso agora, em segundos |
| `freeFlowTravelTime` | tempo de percurso em condicao ideal |
| `confidence` | confianca da medicao, de 0 a 1 |
| `frc` | classe funcional da via, de FRC0 a FRC6 |
| `roadClosure` | indica via interditada |

O comprimento do segmento nao vem explicito, entao ele e derivado de
`freeFlowSpeed * freeFlowTravelTime / 3,6`, o que permite normalizar o atraso por quilometro e
comparar trechos de tamanhos diferentes.

O plano gratuito da TomTom permite 20 mil requisicoes por mes para esse produto, sem cartao de
credito, e responde `429` quando o limite estoura. Esse teto e a restricao central do desenho e
esta documentado na [pagina de precos](https://docs.tomtom.com/pricing).

## Calibracao do zoom

O parametro de zoom da URL nao controla so a escala do mapa, ele decide a hierarquia viaria a
que o ponto sera associado. O mesmo par de coordenadas, na frente do CEI Zona Sul, retorna:

| Zoom | Classe | Comprimento | Velocidade livre |
| --- | --- | --- | --- |
| 10 | FRC2 | 7,41 km | 70 km/h |
| 11 e 12 | FRC5 | 0,44 km | 20 km/h |
| 13 e acima | FRC6 | 3,42 km | 35 km/h |

Em zoom 10 o ponto cola na BR-101, que passa perto, e a medicao perde o sentido. Em zoom 12 ele
isola o trecho de 444 metros em frente ao portao, que e exatamente o objeto do estudo. Por isso
cada segmento guarda o seu proprio zoom no catalogo, e o comando `transito calibrar` existe para
conferir, com uma requisicao por segmento, se a associacao continua correta ao longo do tempo.

## Amostragem e orcamento

O catalogo em [`config/segmentos.yaml`](../config/segmentos.yaml) organiza os segmentos em lotes,
e cada lote tem a sua cadencia por janela do dia. O lote piloto de Nova Parnamirim roda a cada 15
minutos nos tres picos, inclusive no fim de semana, porque o efeito escolar so se comprova por
contraste com o sabado e o domingo. Os lotes de Natal rodam a cada 20 e 30 minutos, restritos a
dias uteis.

O modulo de orcamento projeta o consumo antes de qualquer chamada, aplicando margem de seguranca
de 15% sobre o teto mensal. A projecao atual:

| Lote | Segmentos | Coletas por dia | Requisicoes por mes |
| --- | --- | --- | --- |
| nova-parnamirim | 5 | 36 | 5580 |
| natal-zona-sul | 8 | 26 | 4784 |
| natal-zona-norte | 6 | 18 | 2484 |
| total | 19 | | 12848, ou 64,2% do limite |

Os lotes entram em operacao de forma escalonada, nao todos de uma vez. Enquanto so o piloto
estiver ativo, o consumo fica em 27,9% do limite, o que deixa folga para recalibragem e para
rodadas manuais de teste.

## Metricas

As metricas seguem a nomenclatura usual de engenharia de trafego, para que o resultado seja
comparavel com a literatura e nao com uma escala inventada.

**Indice de tempo de viagem**, ou Travel Time Index, e `tempo_atual / tempo_livre`. Vale 1,0 em
via livre e 1,5 quando a viagem demora 50% a mais do que deveria. O projeto considera o trecho
congestionado a partir de 1,3.

**Atraso por quilometro** e o tempo perdido em relacao ao fluxo livre dividido pelo comprimento do
segmento. Serve para comparar um trecho de 444 metros com um de 7 quilometros.

**Indice de planejamento**, ou Planning Time Index, e o percentil 95 do indice. Ele responde
quanto tempo a pessoa precisa reservar para chegar no horario em 19 de cada 20 dias, que e a
pergunta pratica de quem usa a via.

**Indice de buffer** e `(percentil 95 - media) / media`, e mede a imprevisibilidade. Dois
corredores podem ter a mesma media e experiencias muito diferentes: o de buffer alto e o que
obriga a sair de casa mais cedo por precaucao.

**Nivel de servico** classifica a razao entre velocidade atual e velocidade livre em faixas de A a
F, com A acima de 0,85 e F abaixo de 0,25.

## Clima

Cada rodada registra tambem chuva, temperatura e vento pela
[Open-Meteo](https://open-meteo.com/), que e gratuita e dispensa chave. A analise cruza as duas
series por hora para medir quanto a precipitacao piora o indice, efeito conhecido em Natal mas
raramente quantificado.

## Limitacoes

O dado da TomTom vem de dispositivos conectados, nao de contagem volumetrica na via. Ele mede
velocidade de quem passou, nao quantidade de veiculos, entao uma via vazia e uma via saturada com
semaforo bem programado podem apresentar velocidades parecidas. A amostra tambem depende da
penetracao de dispositivos na regiao, que tende a ser menor em bairros perifericos, e o campo
`confidence` e o unico indicador disso.

A velocidade de fluxo livre e uma referencia calculada pela propria TomTom, nao o limite legal da
via. Quando o fluxo livre de um trecho e 20 km/h, como no caso do segmento do portao da escola,
isso ja indica uma via que nunca foi rapida, e o indice mede a piora sobre esse patamar baixo.

A coleta so acontece nas janelas configuradas, entao a serie nao cobre o dia inteiro com a mesma
densidade. Rodadas agendadas pelo GitHub Actions podem atrasar alguns minutos em horario de pico
da plataforma, o que o campo de horario de coleta registra fielmente.

Por fim, correlacao nao e causa. Se o indice cai depois de uma intervencao, o repositorio mostra
que caiu, nao que a intervencao foi a razao.

## Reproduzir

```bash
uv sync
cp .env.example .env
uv run transito orcamento
uv run transito calibrar --lote nova-parnamirim
uv run transito coletar --forcar
uv run transito analisar
uv run transito relatorio
```

A chave da TomTom vai no `.env`, que esta no `.gitignore`, e no segredo `TOMTOM_API_KEY` do
repositorio para a coleta agendada. A branch `dados` guarda a serie em parquet e precisa existir
antes do primeiro agendamento:

```bash
git switch --orphan dados
mkdir -p raw && touch raw/.gitkeep
git add raw && git commit -m "chore: inicia a branch de dados"
git push -u origin dados && git switch main
```
