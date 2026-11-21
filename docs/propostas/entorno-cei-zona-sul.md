# Entorno do CEI Zona Sul, Avenida Maria Lacerda Montenegro

## O problema

O CEI Zona Sul fica na Avenida Maria Lacerda Montenegro, 260, em Nova Parnamirim, Parnamirim.
A avenida e o eixo que liga o bairro a Avenida Ayrton Senna e a BR-101, entao ela acumula duas
funcoes que brigam entre si: corredor de passagem e porta de escola. Nos horarios de entrada e
saida, o embarque e desembarque acontece na propria pista, e a fila ocupa a faixa de rolamento
justamente quando o fluxo de passagem esta no pico.

A primeira medicao do projeto, feita as 10h34 de uma sexta-feira, fora de qualquer pico, ja
registrou 13 km/h contra 20 km/h de fluxo livre no trecho de 444 metros em frente ao portao,
indice de 1,54 e nivel de servico C. No mesmo instante, o corredor inteiro da avenida marcava
1,20 e a Abel Cabral, rota alternativa paralela, marcava 1,00. O gargalo e local, nao sistemico,
o que e uma boa noticia: problema local admite solucao local e barata.

A serie coletada pelo repositorio existe para responder tres perguntas antes de qualquer obra:

1. O pico do portao coincide com o pico geral da avenida ou e um evento proprio?
2. A fila do portao transborda para o corredor inteiro e para a Abel Cabral?
3. O padrao some no fim de semana e nas ferias, o que confirmaria a origem escolar?

A terceira pergunta e a mais importante, e e por isso que o lote piloto coleta tambem sabado e
domingo, apesar do custo em requisicoes. Sem o contrafactual do fim de semana, qualquer proposta
vira palpite.

## Medidas, da mais embasada para a menos

### Escalonamento dos horarios de entrada e saida

Esta e a medida com melhor evidencia causal e custo proximo de zero. Um estudo de diferencas em
diferencas na China estimou que o trajeto casa-escola aumenta em 4,5 pontos percentuais a
probabilidade de congestionamento numa via, com efeito maior na entrada do que na saida, e
concluiu que escalonar horarios reduz o problema
([School runs and urban traffic congestion](https://www.sciencedirect.com/science/article/pii/S016604622030291X)).
Simulacoes em Bangkok projetam reducoes de 26% a 32% no tempo total de viagem com deslocamentos
de uma a duas horas, mas e simulacao, nao medicao de campo
([Identifying Impacts of School-Escorted Trips](https://doi.org/10.3390/su152316244)).

Na pratica, significa separar a entrada da educacao infantil, do fundamental e do medio em
faixas de 15 a 20 minutos. Depende apenas da escola, nao do poder publico. E a primeira coisa a
tentar, e a serie do repositorio consegue medir o antes e o depois.

### Baia de embarque e desembarque fora da faixa de rolamento

A fila sai da pista e entra em um recuo, com fluxo continuo e sem manobra de retorno. A evidencia
especifica de projeto de baia escolar e fraca na literatura revisada por pares, o que encontrei
foram modelos de fila: um modelo `Mt/D/1/K` aplicado a esse tipo de gargalo reporta queda da fila
maxima media de cerca de 12,4 para 3,5 veiculos quando a chegada e regulada
([Time-Dependent Queuing Model](https://arxiv.org/pdf/2501.14132)). Vale como ordem de grandeza,
nao como promessa.

Exige espaco no lote da escola ou acordo com a prefeitura de Parnamirim para o recuo no
alinhamento. Custo medio, efeito direto sobre a causa.

### Rua escolar, restricao temporaria do trecho

A rua escolar fecha o trecho em frente a escola nos minutos de entrada e saida. E a medida com
mais estudos publicados. Um levantamento com oito escolas em Barcelona observou queda media de
cerca de 80% no fluxo motorizado, chegando perto de 90% nas ruas de restricao total, e reducao de
2% a 7% no dioxido de nitrogenio
([UAB Barcelona](https://www.uab.cat/web/newsroom/news-detail/school-zone-traffic-calming-measures-promote-citizen-health-and-coexistence-1345830290613.html?detid=1345902929044)).
Uma revisao de 16 estudos concluiu que o trafego cai no periodo de restricao e que o
deslocamento para vias vizinhas, quando ocorre, nao gerou problema de seguranca ou foi mitigavel
([School Streets and Traffic Displacement](https://www.walkwheelcycletrust.org.uk/media/10843/school-streets-and-traffic-displacement-technical-report.pdf)).

A evidencia sobre mobilidade ativa e contraditoria. Um estudo britanico com quase 500 escolas
associou o esquema a 6% mais deslocamento ativo
([University of Birmingham](https://www.birmingham.ac.uk/news/2025/school-street-closures-boost-active-travel-to-school-major-uk-study-finds)),
enquanto uma avaliacao quase experimental publicada no BMC Public Health nao encontrou mudanca em
viagens ativas, satisfacao ou percepcao de seguranca
([BMC Public Health](https://link.springer.com/article/10.1186/s12889-025-23236-8)).

O complicador aqui e que a Maria Lacerda Montenegro e corredor de ligacao, nao rua local. Fechar
o trecho empurraria o fluxo de passagem para a Abel Cabral, e por isso a Abel Cabral esta no lote
piloto desde o inicio: se a medida for proposta, o repositorio ja tera a linha de base dela.

### Tratamento de area escolar segundo a norma brasileira

Sinalizacao vertical e horizontal de area escolar, travessia elevada, reducao de velocidade
regulamentada e faixa com boa visibilidade. A referencia nacional e o volume de
[sinalizacao de areas escolares do Manual Brasileiro de Sinalizacao de Transito](https://observatoriodabicicleta.org.br/acervo/manual-brasileiro-de-sinalizacao-de-transito-sinalizacao-de-areas-escolares/),
e o
[Guia de Entornos Escolares Seguros](https://observatoriodabicicleta.org.br/acervo/guia-de-entorno-escolares-seguros/),
produzido pelo Banco Mundial com ITDP Brasil e WRI Brasil, reune as recomendacoes de projeto.

Essas medidas atacam seguranca antes de fluidez, e as duas coisas nao andam sempre juntas: uma
travessia elevada reduz velocidade de proposito. Vale avaliar com esse entendimento, porque o
objetivo no entorno de escola e menos atropelamento, nao mais velocidade.

### Transporte escolar e caronas organizadas

Cada onibus escolar lotado tira varios carros do portao. O
[programa A Caminho da Escola 2.0](https://itdpbrasil.org/wp-content/uploads/2022/05/A-Caminho-da-Escola_2.0-Acao-Piloto.pdf)
do ITDP Brasil traz um metodo de mapa de risco do trajeto casa-escola-casa, contando recorrencia
e gravidade dos 13 conflitos mais comuns entre pedestre e veiculo em area escolar, e usa a
ferramenta Star Rating for Schools para classificar a seguranca da via. E a medida de maior
efeito potencial e de implantacao mais lenta, porque depende de adesao das familias.

## O que o repositorio consegue provar e o que nao consegue

Consegue mostrar o perfil horario do trecho, o contraste entre dia util e fim de semana, o
transbordamento para as vias vizinhas, o efeito da chuva e a variacao antes e depois de uma
intervencao datada.

Nao consegue contar veiculos, separar carro de moto, medir fila em metros, nem atribuir
causalidade. Para isso seria necessaria contagem em campo, que e trabalho de uma manha com
prancheta e cronometro, e que combina bem com a serie automatica: a contagem calibra o que o
sensor remoto nao ve.
