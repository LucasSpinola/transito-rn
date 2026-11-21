# Metodologia

## Por que o projeto gera o próprio dado

Nenhum município do Rio Grande do Norte publica série aberta de congestionamento, e fora de Natal
não existe sequer um portal de mobilidade. Na capital, o portal de dados abertos
([dadosabertos.natal.br](http://dadosabertos.natal.br/)) entrega o catálogo estático de linhas,
terminais e itinerários, e a API dinâmica exige cadastro prévio de desenvolvedor. O anuário
estatístico de sinistros mais recente publicado pela STTU na
[página de publicações](https://natal.rn.gov.br/sttu/publicacoes) é de 2018, e os números de 2024
e 2025 circulam apenas pela imprensa citando a secretaria. Os endereços `dados.natal.br` e
`dados.sttu.natal.br` não respondiam quando este projeto foi montado.

Sinistro também não é congestionamento. Um bairro pode liderar o ranking de acidentes e ter
fluxo livre, enquanto outro trava todo dia sem registrar ocorrência. São duas perguntas
diferentes, e o projeto responde cada uma com a fonte adequada: lentidão com medição própria,
risco com a base de sinistros da PRF.

## Fonte primária

A coleta usa o endpoint [Flow Segment Data](https://docs.tomtom.com/traffic-api/documentation/traffic-flow/flow-segment-data)
da TomTom, que devolve, para um ponto geográfico, o segmento viário correspondente com:

| Campo | Significado |
| --- | --- |
| `currentSpeed` | velocidade média observada agora no segmento |
| `freeFlowSpeed` | velocidade esperada em condição ideal, sem trânsito |
| `currentTravelTime` | tempo de percurso agora, em segundos |
| `freeFlowTravelTime` | tempo de percurso em condição ideal |
| `confidence` | confiança da medição, de 0 a 1 |
| `frc` | classe funcional da via, de FRC0 a FRC6 |
| `roadClosure` | indica via interditada |

O comprimento do segmento não vem explícito, então ele é derivado de
`freeFlowSpeed * freeFlowTravelTime / 3,6`, o que permite normalizar o atraso por quilômetro e
comparar trechos de tamanhos diferentes.

O plano gratuito da TomTom permite 20 mil requisições por mês para esse produto, sem cartão de
crédito, e responde `429` quando o limite estoura. Esse teto é a restrição central do desenho e
está documentado na [página de preços](https://docs.tomtom.com/pricing).

## Calibração do zoom

O parâmetro de zoom da URL não controla só a escala do mapa, ele decide a hierarquia viária à
qual o ponto será associado. O mesmo par de coordenadas, em frente ao CEI Zona Sul, retorna:

| Zoom | Classe | Comprimento | Velocidade livre |
| --- | --- | --- | --- |
| 10 | FRC2 | 7,41 km | 70 km/h |
| 11 e 12 | FRC5 | 0,44 km | 20 km/h |
| 13 e acima | FRC6 | 3,42 km | 35 km/h |

Em zoom 10 o ponto cola na BR-101, que passa perto, e a medição perde o sentido. Em zoom 12 ele
isola o trecho de 444 metros em frente ao portão, que é exatamente o objeto do estudo. Por isso
cada segmento guarda o seu próprio zoom no catálogo, e o comando `transito calibrar` existe para
conferir, com uma requisição por segmento, se a associação continua correta ao longo do tempo.

## Amostragem e orçamento

O catálogo em [`config/segmentos.yaml`](../config/segmentos.yaml) organiza os segmentos em lotes,
e cada lote tem a sua cadência por janela do dia. O lote piloto de Nova Parnamirim roda a cada 15
minutos nos três picos, inclusive no fim de semana, porque o efeito escolar só se comprova por
contraste com o sábado e o domingo. As quatro zonas de Natal e a região metropolitana rodam a cada
30 minutos em dias úteis, Mossoró e os centros do interior a cada 60, e os trechos rodoviários a
cada 120. Largura e resolução disputam a mesma cota, e a escolha foi cobrir o estado com menos
detalhe fino, exceto no lote piloto.

O módulo de orçamento projeta o consumo antes de qualquer chamada, aplicando margem de segurança
de 15% sobre o teto mensal. A projeção atual:

| Lote | Segmentos | Coletas por dia | Requisições por mês |
| --- | --- | --- | --- |
| parnamirim-cei | 3 | 36 | 3348 |
| natal-zona-sul | 5 | 17 | 1955 |
| natal-zona-leste | 6 | 17 | 2346 |
| natal-zona-norte | 6 | 17 | 2346 |
| natal-zona-oeste | 5 | 17 | 1955 |
| regiao-metropolitana | 6 | 17 | 2346 |
| mossoro | 4 | 17 | 1564 |
| acessos-rodoviarios | 2 | 3 | 138 |
| total | 37 | | 15998, ou 80% do limite |

Os lotes entram em operação de forma escalonada, não todos de uma vez. Enquanto só o piloto
estiver ativo, o consumo fica em 16,7% do limite, o que deixa folga para recalibragem e para
rodadas manuais de teste.

## Cobertura de sonda, e por que o interior ficou de fora

O dado da TomTom depende de dispositivos conectados circulando na via. Onde não há penetração
suficiente, a API não devolve erro, devolve o valor histórico de fluxo livre como se fosse a
medição atual. A assinatura disso é `currentSpeed` exatamente igual a `freeFlowSpeed` com
`confidence` igual a 1.

Uma rodada de calibração em 21 de novembro de 2026, às 11h56, horário de pico do almoço, mediu
treze pontos de uma vez:

| Ponto | Resultado | Confiança |
| --- | --- | --- |
| Portão do CEI, Nova Parnamirim | 15 de 20 km/h, índice 1,15 | 0,84 |
| Avenida Alberto Maranhão, Mossoró | 25 de 30 km/h, índice 1,20 | abaixo de 1 |
| Caicó, Assu, Pau dos Ferros, Currais Novos | atual igual ao fluxo livre | 1 |
| BR-304 em Assu, BR-226 em Currais Novos, BR-405 em Pau dos Ferros | atual igual ao fluxo livre | 1 |

Uma leitura isolada não distingue com certeza via genuinamente livre de resposta estática. O que
pesa é o padrão: nenhum ponto do interior variou, enquanto no mesmo instante a capital e Mossoró
variaram. Gastar cota mensal em pontos que devolvem sempre o mesmo número produziria série sem
informação, então os quatro centros do interior e os três trechos rodoviários distantes saíram do
catálogo, e a cota voltou para onde existe sinal: dois segmentos novos em Natal e Mossoró subindo
de 60 para 30 minutos de cadência.

Isso é uma limitação da fonte, não do interior. Caicó e Pau dos Ferros têm congestionamento real,
só não têm quem o registre. Medir ali exigiria contagem em campo ou convênio para acesso a dados
de operadora, e fica registrado como trabalho futuro. A base de sinistros da PRF continua cobrindo
o estado inteiro, então o interior segue presente no diagnóstico de risco, ainda que ausente do de
lentidão.

## Métricas

As métricas seguem a nomenclatura usual de engenharia de tráfego, para que o resultado seja
comparável com a literatura e não com uma escala inventada.

**Índice de tempo de viagem**, ou Travel Time Index, é `tempo_atual / tempo_livre`. Vale 1,0 em
via livre e 1,5 quando a viagem demora 50% a mais do que deveria. O projeto considera o trecho
congestionado a partir de 1,3.

**Atraso por quilômetro** é o tempo perdido em relação ao fluxo livre dividido pelo comprimento
do segmento. Serve para comparar um trecho de 444 metros com um de 7 quilômetros.

**Índice de planejamento**, ou Planning Time Index, é o percentil 95 do índice. Ele responde
quanto tempo a pessoa precisa reservar para chegar no horário em 19 de cada 20 dias, que é a
pergunta prática de quem usa a via.

**Índice de buffer** é `(percentil 95 - média) / média`, e mede a imprevisibilidade. Dois
corredores podem ter a mesma média e experiências muito diferentes: o de buffer alto é o que
obriga a sair de casa mais cedo por precaução.

**Nível de serviço** classifica a razão entre velocidade atual e velocidade livre em faixas de A
a F, com A acima de 0,85 e F abaixo de 0,25.

## Sinistros em rodovias federais

A segunda fonte é a base de acidentes da Polícia Rodoviária Federal, publicada em
[dados abertos da PRF](https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf),
com arquivos anuais de 2007 a 2026 no recorte agrupado por ocorrência. Cada linha traz data, UF,
BR, quilômetro, município, causa, tipo, classificação, fase do dia, condição meteorológica e
contagem de vítimas, além de latitude e longitude.

A ingestão é manual de propósito. Os arquivos ficam em links do Google Drive com identificador
opaco, sem padrão de URL, e o domínio `dados.prf.gov.br` não resolve, então automatizar o download
seria frágil e quebraria na primeira republicação. O fluxo é baixar os CSV, salvar em
`data/externo/prf/` e rodar `transito importar-prf`.

O importador exige apenas o núcleo do esquema, que são data, UF, BR, quilômetro, município, causa,
tipo, classificação e mortos, e preenche com nulo qualquer coluna ausente. Isso importa porque o
esquema mudou entre o sistema BR-Brasil, usado até 2016, e o BAT, usado de 2017 em diante.
Quilômetro, latitude e longitude vêm com vírgula decimal e são convertidos na leitura.

A análise rankeia trechos em faixas de dez quilômetros por BR, municípios, causas e fase do dia, e
cruza cada sinistro com os segmentos monitorados por distância geodésica, o que permite perguntar
quantas mortes aconteceram num raio de cinco quilômetros de um ponto que também é medido por
velocidade.

Duas ressalvas pesam. A base cobre só rodovias federais, então sinistro em via municipal não
aparece, e Natal fica subrepresentada fora da BR-101 e da BR-226. E contagem bruta de ocorrência
não é risco: um trecho movimentado acumula acidente por exposição, não por perigo. Por isso o
projeto também calcula letalidade por ocorrência, que é a razão entre mortes e sinistros.

## Volume de veículos, uma lacuna assumida

O ideal seria cruzar lentidão e sinistro com volume real de veículos. O Plano Nacional de Contagem
de Tráfego do DNIT existe para isso, com equipamentos de contagem contínua na malha federal, mas
a [página oficial](https://www.gov.br/dnit/pt-br/assuntos/planejamento-e-pesquisa/planejamento/contagem-de-trafego)
foi atualizada pela última vez em 2020, o portal de downloads não oferece arquivo algum e o único
conjunto baixável é uma planilha de 1994 a 2001. O projeto registra isso como limitação, não como
fonte.

## Clima

Cada rodada registra também chuva, temperatura e vento pela
[Open-Meteo](https://open-meteo.com/), que é gratuita e dispensa chave. A análise cruza as duas
séries por hora para medir quanto a precipitação piora o índice, efeito conhecido em Natal mas
raramente quantificado.

## Limitações

O dado da TomTom vem de dispositivos conectados, não de contagem volumétrica na via. Ele mede
velocidade de quem passou, não quantidade de veículos, então uma via vazia e uma via saturada
com semáforo bem programado podem apresentar velocidades parecidas. A amostra também depende da
penetração de dispositivos na região, que tende a ser menor em bairros periféricos, e o campo
`confidence` é o único indicador disso.

A velocidade de fluxo livre é uma referência calculada pela própria TomTom, não o limite legal
da via. Quando o fluxo livre de um trecho é 20 km/h, como no caso do segmento em frente ao
portão da escola, isso já indica uma via que nunca foi rápida, e o índice mede a piora sobre esse
patamar baixo.

A coleta só acontece nas janelas configuradas, então a série não cobre o dia inteiro com a mesma
densidade. Rodadas agendadas pelo GitHub Actions atrasam com frequência, às vezes dezenas de
minutos, porque o agendador da plataforma é melhor esforço. Por isso a cadência não olha o relógio
e sim o tempo decorrido desde a última amostra de cada lote: uma execução atrasada ainda coleta, e
uma execução adiantada não duplica. O horário real de cada medição fica gravado na amostra.

Por fim, correlação não é causa. Se o índice cai depois de uma intervenção, o repositório mostra
que caiu, não que a intervenção foi a razão.

## Reproduzir

```bash
uv sync
cp .env.example .env
uv run transito orcamento
uv run transito calibrar --lote nova-parnamirim
uv run transito coletar --forcar
uv run transito analisar
uv run transito importar-prf
uv run transito sinistros
uv run transito relatorio
```

A chave da TomTom vai no `.env`, que está no `.gitignore`, e no segredo `TOMTOM_API_KEY` do
repositório para a coleta agendada. A branch `dados` guarda a série em parquet e precisa existir
antes do primeiro agendamento:

```bash
git switch --orphan dados
mkdir -p raw && touch raw/.gitkeep
git add raw && git commit -m "chore: inicia a branch de dados"
git push -u origin dados && git switch main
```
