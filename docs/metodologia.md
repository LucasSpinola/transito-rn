# Metodologia

## Por que o projeto gera o próprio dado

Natal não publica série aberta de congestionamento. O portal de dados abertos da mobilidade
([dadosabertos.natal.br](http://dadosabertos.natal.br/)) entrega o catálogo estático de linhas,
terminais e itinerários, e a API dinâmica exige cadastro prévio de desenvolvedor. O anuário
estatístico de sinistros mais recente publicado pela STTU na
[página de publicações](https://natal.rn.gov.br/sttu/publicacoes) é de 2018, e os números de 2024
e 2025 circulam apenas pela imprensa citando a secretaria. Os endereços `dados.natal.br` e
`dados.sttu.natal.br` não respondiam quando este projeto foi montado.

Sinistro também não é congestionamento. Um bairro pode liderar o ranking de acidentes e ter
fluxo livre, enquanto outro trava todo dia sem registrar ocorrência. Como nenhuma base pública
mede tempo de viagem em Natal, o repositório constrói a sua.

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
contraste com o sábado e o domingo. Os lotes de Natal rodam a cada 20 e 30 minutos, restritos a
dias úteis.

O módulo de orçamento projeta o consumo antes de qualquer chamada, aplicando margem de segurança
de 15% sobre o teto mensal. A projeção atual:

| Lote | Segmentos | Coletas por dia | Requisições por mês |
| --- | --- | --- | --- |
| nova-parnamirim | 5 | 36 | 5580 |
| natal-zona-sul | 8 | 26 | 4784 |
| natal-zona-norte | 6 | 18 | 2484 |
| total | 19 | | 12848, ou 64,2% do limite |

Os lotes entram em operação de forma escalonada, não todos de uma vez. Enquanto só o piloto
estiver ativo, o consumo fica em 27,9% do limite, o que deixa folga para recalibragem e para
rodadas manuais de teste.

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
densidade. Rodadas agendadas pelo GitHub Actions podem atrasar alguns minutos em horário de pico
da plataforma, o que o campo de horário de coleta registra fielmente.

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
