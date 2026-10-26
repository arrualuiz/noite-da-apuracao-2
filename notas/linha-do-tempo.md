# Linha do tempo da noite · 25/10/2026

Tudo o que fiz na noite do 2º turno, na ordem, com onde ver cada coisa. Cada melhoria virou um commit
próprio (a hora é a do commit). Os links `127.0.0.1:5500` abrem pelo Live Server do VS Code com a pasta
do projeto aberta.

## Onde ver tudo

| O quê | Link |
|---|---|
| Painel da noite (expectativa x apuração, previsão, Minas, perguntas) | http://127.0.0.1:5500/painel/perguntas.html (gerado pelo coletor, fica só no PC) |
| Depois da apuração (Curitiba, ilhas, previsão, transferência, abstenção, extremos) | http://127.0.0.1:5500/painel/depois.html |
| Curitiba, escola por escola (com busca) | http://127.0.0.1:5500/painel/depois.html#curitiba |
| Ilhas | http://127.0.0.1:5500/painel/depois.html#ilhas |
| A previsão olhando para trás | http://127.0.0.1:5500/painel/depois.html#previsao |
| **O site publicado (GitHub Pages)** | https://arrualuiz.github.io/noite-da-apuracao-2/ |
| Curitiba no site (mapa por bairro, escolas e o voto desde 2002) | https://arrualuiz.github.io/noite-da-apuracao-2/painel/curitiba.html |
| Diário da noite (palpites, virada, resultado, olhando para trás) | [notas.md](notas.md) |
| Rascunho do post do LinkedIn | [post-linkedin.md](post-linkedin.md) |
| Plano em sprints | [../PLANO.md](../PLANO.md) |
| Repositório | https://github.com/arrualuiz/noite-da-apuracao-2 |

## Antes da apuração

- **19h15** · Liguei o coletor do TSE do 2º turno (eleição 6258), a cada 60 segundos.
- **19h16** · Meus palpites, antes de qualquer número: o Lula ganha com margem menor que a de 2022 e a abstenção vai ser maior. Commit **19h24**.
- **19h28** · Defini as perguntas da noite: para onde foram os votos dos outros candidatos, quem ganha Minas, se algum estado do Sul mudou de lado, o Nordeste em votos e o comparecimento. Organizei o projeto em sprints. Commit **19h34**.

## Durante a apuração

- **19h45** · Painel das perguntas da noite, com a previsão do resultado final.
- **19h48** · Card "Dá para afirmar o resultado?", com o erro da previsão medido no 1º turno.
- **19h55** · Repositório publicado no GitHub. O coletor passou a enviar os dados sozinho a cada 30 min.
- **19h57** · Crescimento do Lula por estado: mapa, e a virada somada contra a diferença do 1º turno.
- **20h04** · As 11 pesquisas da última semana e a média delas (Lula 49,2%) no gráfico da previsão.
- **20h14** · Segundo palpite, com 34,45% apurado: Lula 50,2 x Flávio 49,8 e abstenção igual à de 2022 (corrigido às 20h15, porque falei 51,2 e a soma dava 101%).
- **20h19** · `agora.py`: onde falta apurar, e o Lula agora x o mesmo ponto do 1º turno.
- **20h22** · Capital x Grande SP x interior (e Rio e BH), e as trocas de liderança em Minas.
- **20h25** · **A virada:** o Lula passa o Flávio no placar, com 48,1% apurado. Commit **20h26**, com a abstenção de todas as cidades nos dois turnos.
- **20h30** · `trajetoria.py`: o caminho provável do placar até 100%.
- **20h32** · Gráfico "minha expectativa x a apuração", no estilo do UOL: linha cheia para o real, tracejado para o cálculo e pontilhado para o meu palpite.
- **20h48** · Mapa de quem lidera, mapa do crescimento e o gráfico do 1º para o 2º turno por estado. Nas notas: a previsão subia sem parar, sinal de viés.
- **21h03** · Notas: o que os dados responderam às 21h02.
- **21h05** · `curiosidades.py`: os números absurdos (empate de 1.530 x 1.530 em Marquinho-PR, cidades que viraram).
- **21h08** · `transferencia.py`: o Brasil em pessoas e para onde foram os eleitores do Cury, do Renan e do Caiado.
- **21h09** · **Lula eleito.** O TSE marcou o resultado como matematicamente definido com 97,69% das seções. Commit **21h12**.

## Depois do resultado (voltei às 22h16)

- **22h20** · Números quase finais (Lula 51,78% x 48,22%, 4,43 milhões de votos) e **a previsão olhando para trás** (`retroativo.py`). Meu modelo previu menos Lula a noite toda, e o erro veio sobretudo de São Paulo. O método "mesmo ponto do 1º turno" teria errado menos desde os 20%.
- **23h03** · `extremos.py`: o menor e o maior de cada coisa medida, e quem é cada registro (cidade e estado).
- **23h12** · Cards "Minas, o espelho do Brasil": 8 de 8 disputas desde 2002 com o mesmo vencedor.
- **23h19** · `ilhas.py`: cidades que votaram muito diferente das 10 vizinhas. As ilhas vermelhas são terras indígenas, universidades e periferias; as azuis, polos do agro e colônias europeias. Usei o centroide do IBGE porque o cadastro do TSE tem coordenadas erradas (Luislândia-MG aparecia no Sul de Minas).
- **23h20** · `bairros.py`: **Curitiba por bairro e por escola**, lendo o boletim de cada uma das 4.056 urnas nos dois turnos. A soma bate exatamente com o TSE. O Lula ficou na frente em 3 de 69 bairros; cresceu mais na periferia (CIC +10.206 votos); nos bairros ricos, o Flávio ganhou mais votos novos que ele.
- **23h28** · Página **Depois da apuração**, com tudo em gráficos. O coletor fechou: apuração encerrada, 100%.
- **23h29** · Mapa de Curitiba com o contorno do município (IBGE).
- **23h34** · Busca de escola no mapa. A minha, o **Colégio Estadual Professor Narciso Mendes** (Xaxim, 11 seções), foi de 26,7% para 31,6% de Lula: a 13ª de 405 escolas em que o Lula mais cresceu.

- **23h41** · Esta linha do tempo. **23h48** · As pendências que saíram da noite foram para o `PLANO.md`.
- **23h59** · **O site no GitHub Pages:** capa (`index.html`), página de Curitiba e página do Brasil, e o painel da noite congelado no resultado final. Na página de Curitiba:
  - o mapa por bairro, pintando cada um dos 75 bairros oficiais (malha do IPPUC), e o mapa por escola com as divisas. Cada escola entra no bairro onde ela fica de fato: em 680 seções, o bairro do cadastro do TSE era outro;
  - **por que Curitiba vota assim**, com `capitais_historia.py`: em 2002, Curitiba deu 64,7% ao Lula, mais que o Brasil. A virada foi em 2006; em 2014, foi a capital que menos votou no PT; em 2018, 76,5% Bolsonaro. Em 2026 (37,7%), votou igual ao Paraná. O porquê (Lava Jato, classe média, imigração) ficou como hipótese, com fontes.

## Depois da meia-noite (26/10)

- **00h01** · Rascunho do post do LinkedIn ([post-linkedin.md](post-linkedin.md)).

## Como fecharam os palpites

- Quem ganha: **acertei, Lula** (a média das pesquisas dava Flávio).
- Margem menor que 2022: **errei.** Foi 3,6 pontos (4,43 milhões de votos), contra 1,8 em 2022.
- Abstenção maior ou igual a 2022: **errei.** Caiu para 19,22%; 2,96 milhões de pessoas a mais foram votar.
- Lula 50,2%: **errei por 1,6 ponto** (deu 51,78%).
