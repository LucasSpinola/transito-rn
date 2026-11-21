# Entorno do CEI Zona Sul, Avenida Maria Lacerda Montenegro

## O problema

O CEI Zona Sul fica na Avenida Maria Lacerda Montenegro, 260, em Nova Parnamirim, Parnamirim.
A avenida é o eixo que liga o bairro à Avenida Ayrton Senna e à BR-101, então ela acumula duas
funções que brigam entre si: corredor de passagem e porta de escola. Nos horários de entrada e
saída, o embarque e desembarque acontece na própria pista, e a fila ocupa a faixa de rolamento
justamente quando o fluxo de passagem está no pico.

A primeira medição do projeto, feita às 10h34 de uma sexta-feira, fora de qualquer pico, já
registrou 13 km/h contra 20 km/h de fluxo livre no trecho de 444 metros em frente ao portão,
índice de 1,54 e nível de serviço C. No mesmo instante, o corredor inteiro da avenida marcava
1,20 e a Abel Cabral, rota alternativa paralela, marcava 1,00. O gargalo é local, não sistêmico,
o que é uma boa notícia: problema local admite solução local e barata.

A série coletada pelo repositório existe para responder três perguntas antes de qualquer obra:

1. O pico do portão coincide com o pico geral da avenida ou é um evento próprio?
2. A fila do portão transborda para o corredor inteiro e para a Abel Cabral?
3. O padrão some no fim de semana e nas férias, o que confirmaria a origem escolar?

A terceira pergunta é a mais importante, e é por isso que o lote piloto coleta também sábado e
domingo, apesar do custo em requisições. Sem o contrafactual do fim de semana, qualquer proposta
vira palpite.

## Medidas, da mais embasada para a menos

### Escalonamento dos horários de entrada e saída

Esta é a medida com melhor evidência causal e custo próximo de zero. Um estudo de diferenças em
diferenças na China estimou que o trajeto casa-escola aumenta em 4,5 pontos percentuais a
probabilidade de congestionamento numa via, com efeito maior na entrada do que na saída, e
concluiu que escalonar horários reduz o problema
([School runs and urban traffic congestion](https://www.sciencedirect.com/science/article/pii/S016604622030291X)).
Simulações em Bangkok projetam reduções de 26% a 32% no tempo total de viagem com deslocamentos
de uma a duas horas, mas é simulação, não medição de campo
([Identifying Impacts of School-Escorted Trips](https://doi.org/10.3390/su152316244)).

Na prática, significa separar a entrada da educação infantil, do fundamental e do médio em
faixas de 15 a 20 minutos. Depende apenas da escola, não do poder público. É a primeira coisa a
tentar, e a série do repositório consegue medir o antes e o depois.

### Baia de embarque e desembarque fora da faixa de rolamento

A fila sai da pista e entra em um recuo, com fluxo contínuo e sem manobra de retorno. A evidência
específica de projeto de baia escolar é fraca na literatura revisada por pares, o que encontrei
foram modelos de fila: um modelo `Mt/D/1/K` aplicado a esse tipo de gargalo reporta queda da fila
máxima média de cerca de 12,4 para 3,5 veículos quando a chegada é regulada
([Time-Dependent Queuing Model](https://arxiv.org/pdf/2501.14132)). Vale como ordem de grandeza,
não como promessa.

Exige espaço no lote da escola ou acordo com a prefeitura de Parnamirim para o recuo no
alinhamento. Custo médio, efeito direto sobre a causa.

### Rua escolar, restrição temporária do trecho

A rua escolar fecha o trecho em frente à escola nos minutos de entrada e saída. É a medida com
mais estudos publicados. Um levantamento com oito escolas em Barcelona observou queda média de
cerca de 80% no fluxo motorizado, chegando perto de 90% nas ruas de restrição total, e redução de
2% a 7% no dióxido de nitrogênio
([UAB Barcelona](https://www.uab.cat/web/newsroom/news-detail/school-zone-traffic-calming-measures-promote-citizen-health-and-coexistence-1345830290613.html?detid=1345902929044)).
Uma revisão de 16 estudos concluiu que o tráfego cai no período de restrição e que o
deslocamento para vias vizinhas, quando ocorre, não gerou problema de segurança ou foi mitigável
([School Streets and Traffic Displacement](https://www.walkwheelcycletrust.org.uk/media/10843/school-streets-and-traffic-displacement-technical-report.pdf)).

A evidência sobre mobilidade ativa é contraditória. Um estudo britânico com quase 500 escolas
associou o esquema a 6% mais deslocamento ativo
([University of Birmingham](https://www.birmingham.ac.uk/news/2025/school-street-closures-boost-active-travel-to-school-major-uk-study-finds)),
enquanto uma avaliação quase experimental publicada no BMC Public Health não encontrou mudança em
viagens ativas, satisfação ou percepção de segurança
([BMC Public Health](https://link.springer.com/article/10.1186/s12889-025-23236-8)).

O complicador aqui é que a Maria Lacerda Montenegro é corredor de ligação, não rua local. Fechar
o trecho empurraria o fluxo de passagem para a Abel Cabral, e por isso a Abel Cabral está no lote
piloto desde o início: se a medida for proposta, o repositório já terá a linha de base dela.

### Tratamento de área escolar segundo a norma brasileira

Sinalização vertical e horizontal de área escolar, travessia elevada, redução de velocidade
regulamentada e faixa com boa visibilidade. A referência nacional é o volume de
[sinalização de áreas escolares do Manual Brasileiro de Sinalização de Trânsito](https://observatoriodabicicleta.org.br/acervo/manual-brasileiro-de-sinalizacao-de-transito-sinalizacao-de-areas-escolares/),
e o
[Guia de Entornos Escolares Seguros](https://observatoriodabicicleta.org.br/acervo/guia-de-entorno-escolares-seguros/),
produzido pelo Banco Mundial com ITDP Brasil e WRI Brasil, reúne as recomendações de projeto.

Essas medidas atacam segurança antes de fluidez, e as duas coisas não andam sempre juntas: uma
travessia elevada reduz velocidade de propósito. Vale avaliar com esse entendimento, porque o
objetivo no entorno de escola é menos atropelamento, não mais velocidade.

### Transporte escolar e caronas organizadas

Cada ônibus escolar lotado tira vários carros do portão. O
[programa A Caminho da Escola 2.0](https://itdpbrasil.org/wp-content/uploads/2022/05/A-Caminho-da-Escola_2.0-Acao-Piloto.pdf)
do ITDP Brasil traz um método de mapa de risco do trajeto casa-escola-casa, contando recorrência
e gravidade dos 13 conflitos mais comuns entre pedestre e veículo em área escolar, e usa a
ferramenta Star Rating for Schools para classificar a segurança da via. É a medida de maior
efeito potencial e de implantação mais lenta, porque depende de adesão das famílias.

## O que o repositório consegue provar e o que não consegue

Consegue mostrar o perfil horário do trecho, o contraste entre dia útil e fim de semana, o
transbordamento para as vias vizinhas, o efeito da chuva e a variação antes e depois de uma
intervenção datada.

Não consegue contar veículos, separar carro de moto, medir fila em metros, nem atribuir
causalidade. Para isso seria necessária contagem em campo, que é trabalho de uma manhã com
prancheta e cronômetro, e que combina bem com a série automática: a contagem calibra o que o
sensor remoto não vê.
