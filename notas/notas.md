# Notas da noite (2º turno, 25/10/2026)

O diário do que fui vendo e pensando durante a apuração. Horários de Brasília.

## 19h15 · Começo

As urnas fecharam às 17h. Liguei o coletor do 1º turno, agora apontado para o 2º turno (código TSE 6258), com uma coleta por minuto.

- **19h16 · TSE com 1,94% das seções:** Lula 51,96% x Flávio 48,04%. Minas com 1,02%.

- **19h28 · 4,24%:** Lula 51,57% x Flávio 48,43%. O Lula vem caindo desde 51,96%. A apuração está desigual: o exterior já tem 60% apurado (Lula 59,7%), a Paraíba 22% (Lula 70%) e o Pará 17%. SP tem 0,1%, o RJ 0%, a Bahia 0,8% e o Ceará 0,5%.
- **Pista do momento:** nos estados com mais de 10% apurado, o Lula está fazendo, em média, 4,5 pontos a mais que a parte dele em Lula + Flávio no 1º turno. Se isso valer no país todo, ele fecha perto de 53%. Se for só metade disso, fecha perto de 51%. Se não valer em nenhum lugar, o Flávio fecha com 51%. Tudo depende de para onde foram os votos dos outros candidatos do 1º turno.

- **19h45 · as perguntas da noite:** para onde foram os votos dos outros candidatos, quem ganha Minas, se algum estado do Sul mudou de lado, se Lula e Flávio cresceram em votos no Nordeste e se o comparecimento mudou. Montei um painel que responde a cada coleta (`painel/perguntas.html`) e uma previsão do resultado final.

- **19h50 · quando dá para afirmar o resultado?** Medi o erro da projeção por estado no 1º turno de 2026, na diferença entre os dois primeiros: 4,1 pontos com 25% apurado, 2,2 com 50%, 1,4 com 70%, 0,7 com 90% e 0,2 com 99%. E o erro foi sempre para o mesmo lado: o voto apurado mais tarde era mais favorável ao Lula. Regra do painel: "provável" quando a vantagem prevista passa do erro típico daquele ponto; "com segurança" quando passa do dobro.

- **19h57 · o crescimento do Lula, estado por estado (20% apurado):** na previsão para 100%, o saldo do Lula (votos dele menos os do Flávio) anda +3,67 milhões em relação ao 1º turno, somando todos os estados. A diferença do 1º turno era Flávio +2,22 milhões, então sobram ~1,44 milhão para o Lula. Ele cresceu em 21 dos 25 estados com pelo menos 3% apurado. As maiores viradas: PE, SC, BA e MG. Contra: SP, RS e AM. Novo bloco no painel, com mapa.

- **20h05 · as pesquisas x a apuração:** as 11 pesquisas da última semana com números publicados (`dados/pesquisas.csv`) davam, em média, Lula 49,2% x Flávio 50,8% dos válidos; só a Vox Brasil tinha o Lula na frente. A previsão das 20h, com 20% apurado, dá Lula ~50,6%: uns 1,4 ponto acima da média das pesquisas, dentro das margens de erro (1 a 2,4 pontos). No 1º turno foi o contrário: a Quaest deu Lula 46% x Flávio 45% e as urnas deram Flávio 47,03% x Lula 45,16%.

- **20h14 · 34,45% apurado:** placar Flávio 50,32% x Lula 49,68%; previsão Lula 50,56%. Abstenção nas seções apuradas: 19,26%. Novo palpite: Lula 50,2% x Flávio 49,8% e abstenção igual à de 2022 (20,58%).

- **20h18 · 39,8% apurado, comparando com o mesmo ponto do 1º turno** (`analise/agora.py`): o Lula está à frente de onde estava no 1º turno em quase todo lugar. SP 42,0% (no mesmo ponto do 1º turno: 38,0%), MG 50,0% (45,7%), Nordeste 68,1% (66,1%), Sul 37,5% (34,9%). Só o RJ está igual, com 3% apurado. Falta apurar: SP é 30% dos eleitores que faltam, o Nordeste 28%, o RJ 13% e MG 11%.

- **20h25 · capital x interior e as trocas em Minas:** o coletor agora baixa também os 39 municípios da Grande SP, o Rio e BH (`coleta/municipios.py`, `dados/segmentos.csv`). Com ~10% apurado, o Lula tem 55,4% na capital paulista (52,5% no 1º turno), 53,6% no resto da Grande SP (48,5%) e 38,1% no interior e litoral (35,1%). Minas já trocou de líder 8 vezes entre as 20h00 e as 20h16, sempre a menos de 0,1 ponto dos 50%.

- **20h25 · VIROU:** na versão das 20:25:30 do TSE, com 48,1% das seções apuradas, o placar passou para **Lula 50,06% x Flávio 49,94%**. O Flávio liderava o placar desde as 19h53. Dava para prever o momento? Uma reta do placar x % apurado, feita com as últimas 10 coletas, errava muito longe da virada (às 20h10 apontava 108%), melhorava às 20h15 (55,5%) e às 20h20 acertou: "49,1% apurado, daqui ~6 min".
- **20h26 · abstenção:** 18,84% no Brasil nas seções já apuradas, contra 20,84% no 1º turno. Caiu em todas as regiões, menos no Norte (21,06% x 19,43%). Baixei os 5.757 arquivos de município dos dois turnos (`analise/abstencao.py`, `dados/abstencao_municipios.csv`). Até agora, das cidades com mais de 50 mil eleitores e 100% apuradas, o Paraná domina as maiores quedas (Sarandi −4,3 pontos, Cambé −4,1, Apucarana −3,4).

- **20h30 · o Lula sobe e depois cai?** Simulei o caminho do placar (`analise/trajetoria.py`): cada estado no ritmo de apuração dos últimos 10 min, com o % do Lula previsto para o que falta. Com 53% das seções, Lula 50,23%. O caminho provável: sobe até ~51,0% por volta das 21h05, quando o Nordeste (CE, PE, PI, BA) e o Sul terminarem, e depois cai uns 0,2 ponto, porque o Rio (11,8 milhões de eleitores faltando, Lula ~45% no que falta) é o mais lento e fica para o fim. Final previsto: ~50,8%.

- **20h35 · meu gráfico, no estilo do UOL:** placar real (linha cheia), o caminho calculado até 100% (tracejado, recalculado a cada coleta e guardado em `dados/trajetorias.csv`), o meu palpite das 20h14 (pontilhado) e o 1º turno (tracejado claro). Com 55,6% apurado, o cálculo termina em Lula 50,80% x Flávio 49,20%; o meu palpite, em 50,2 x 49,8.

- **20h47 · 73% apurado, Lula 51,03%; previsão 51,21%.** A previsão subiu sem parar desde os 30% (50,49 → 50,76 com 50% → 51,18 com 70%). Quando uma previsão anda sempre para o mesmo lado, isso é sinal de viés, não de ruído: o voto que chega mais tarde dentro de cada estado é mais favorável ao Lula, como no 1º turno. Minas, o termômetro (quem venceu lá venceu no Brasil em todos os 2º turnos de 2002 a 2022), está em 50,0%. Gráficos novos: mapa de quem lidera, mapa do crescimento com escala própria e o gráfico do 1º para o 2º turno por estado.

- **21h02 · 89,7% apurado, Lula 51,55%; previsão 51,57%, com erro típico de 0,7 ponto: dá para afirmar com segurança.** O que os dados responderam até aqui:
  1. *Votos dos outros candidatos:* o Lula ganhou 2,7 pontos sobre o 1º turno, em média. Pelo saldo nacional, ficou com ~80% dos votos dos outros (o case 17 dizia que ele precisava de ~65%).
  2. *Minas:* Lula 50,29% com 91% apurado, depois de 10 trocas de liderança. O termômetro deve se manter.
  3. *Sul:* nenhum estado mudou de lado, mas o Lula cresceu ~3 pontos nos três (PR 34,2 → 37,4; SC 27,3 → 30,6; RS 39,1 → 42,3).
  4. *Nordeste:* os dois cresceram em votos, mas o Lula ~7 vezes mais: +2,9 milhões (21,5 → 24,4) contra +0,4 milhão do Flávio (10,4 → 10,8), na previsão para 100%.
  5. *Comparecimento:* 81,2% contra 79,2% no 1º turno. Subiu em todas as regiões, menos no Norte.
  6. *Virada:* +6,1 milhões de saldo para o Lula contra uma diferença de 2,2 milhões no 1º turno.

- **21h05 · números absurdos** (`analise/curiosidades.py`, com 4.436 cidades 100% apuradas): Marquinho (PR) empatou, 1.530 x 1.530. Cinco cidades foram decididas por 1 voto. Carnaubeira da Penha (PE) deu 92,3% para o Lula, e Nova Pádua (RS), 90,6% para o Flávio. 169 cidades mudaram de lado do 1º para o 2º turno, e 168 delas para o Lula (a maior, Ribeirão das Neves-MG). Minas: Lula por 46.336 votos com 94% apurado, menos que um Mineirão lotado e menos até que os 49.650 de 2022. Pico da apuração: 32.717 votos por segundo, perto das 20h34.

- **21h08 · em pessoas** (`analise/transferencia.py`, 95% apurado, levado a 100%): 3,15 milhões de pessoas a mais foram votar (125,3 → 128,4 milhões; abstenção 21,08% → 19,10%). Brancos −871 mil e nulos −964 mil. Para onde foram os eleitores dos outros candidatos, por regressão de Goodman nas 4.718 cidades 100% apuradas, com restrição (cada linha entre 0 e 100%, somando 100%): Cury ~62% Lula e ~36% branco/nulo; Renan ~83% Flávio; Caiado dividido, ~40% Lula e ~55% Flávio. Sem a restrição, 5 dos 32 coeficientes saíam impossíveis (até −77%). E quantas pessoas trocaram Lula por Flávio, ou o contrário, os dados agregados não conseguem separar: o modelo cola em 0% porque não distingue trocar de lado de outras mudanças.

## 🎉 21h09 · LULA ELEITO

**Na versão das 21:09:01 do TSE, com 97,69% das seções apuradas, o resultado ficou matematicamente definido: Luiz Inácio Lula da Silva está reeleito presidente.** Lula 62.641.973 votos (51,74%) x Flávio Bolsonaro 58.436.437 (48,26%), uma diferença de 4,2 milhões de votos.

- O Lula abriu na frente (19h18), o Flávio passou às 19h46 e liderou o placar de ~17% a ~48% apurado. **A virada veio às 20h25**, com 48,1%.
- A previsão para 100% deu Lula o tempo todo, de 50,5% (com 30% apurado) a 51,6% (com 90%). E subiu sem parar: sinal de viés.
- Minas, o termômetro, estava com o Lula por ~46 mil votos às 21h09, depois de 9 trocas de liderança. No fim a diferença mais que dobrou (veja abaixo). Quem venceu em Minas venceu no Brasil de novo.
- **A conta dos meus palpites:** errei a margem (achei que seria menor que a de 2022, mas foi ~3,5 pontos contra 1,8) e errei a abstenção (achei que seria maior ou igual à de 2022, mas caiu para ~19%). Errei o número das 20h14 (50,2%) por ~1,5 ponto. A média das 11 pesquisas (Lula 49,2%) errou por ~2,5 pontos e apontava o Flávio na frente; eu acertei quem ganhava.

## 22h17 · Números quase finais (99,99% das seções) e olhando para trás

**Placar:** Lula 64.249.053 (51,78%) x Flávio 59.822.251 (48,22%), com 4.426.802 votos de diferença. Em 2022 a diferença foi de 2,14 milhões, então agora foi o dobro.

**Minas:** Lula 6.345.135 (50,42%) x Flávio 6.238.495, com 106.640 votos de diferença e 99,9% apurado. Em 2022 foram 49.650. A diferença às 21h09 (~46 mil) ainda não era a final.

**Quem foi votar** (em % e em pessoas):
- Abstenção de 19,22% (30,5 milhões de pessoas), contra 21,08% no 1º turno e 20,58% no 2º turno de 2022. Votaram **2,96 milhões de pessoas a mais** que no 1º turno.
- Brancos caíram de 2,30 para 1,43 milhão (-870 mil). Nulos caíram de 3,67 para 2,72 milhões (-951 mil).
- A abstenção caiu em quase todo lugar. Na capital de São Paulo foi de 23,4% para 20,4% (1,86 milhão de faltosos), em Salvador de 20,1% para 15,8%, e a Bahia teve as maiores quedas (Lauro de Freitas -5,6 pts, Camaçari -4,9).
- **A exceção foi o Norte:** em Macapá subiu +6,0 pts, em Santana (AP) +6,2 e em Cruzeiro do Sul (AC) +6,6, além de Breves e Oriximiná (PA) e Itacoatiara (AM). Ainda não sei por quê. Fica para a sprint 1.

**Números absurdos (5.562 cidades 100% apuradas):**
- Empate perfeito em Marquinho (PR), com 1.530 x 1.530. Cinco cidades foram decididas por **1 voto**: Apiacá (ES), Anhanguera (GO), Altamira do Paraná (PR), Nova Luzitânia (SP) e São João do Pau d'Alho (SP).
- As cidades mais de um lado só foram Carnaubeira da Penha (PE), com 92,3% para o Lula, e Nova Pádua (RS), com 90,6% para o Flávio.
- **212 cidades mudaram de lado** do 1º para o 2º turno: 211 para o Lula e 1 para o Flávio. A maior foi o Rio de Janeiro capital (47,8% → 51,5%), seguida de Osasco, Ananindeua, Macapá e São Vicente.
- A cidade de São Paulo deu ao Lula 766 mil votos de vantagem e Curitiba deu ao Flávio 277 mil.
- No pico, perto das 20h34, a apuração contou 32.717 votos válidos por segundo, ou ~2 milhões por minuto.

**Para onde foram os votos do 1º turno** (regressão de Goodman com restrição, em todas as 5.562 cidades; é estimativa):
- **Cury** (3,45 mi): ~55% Lula (1,9 mi), ~3% Flávio, ~41% branco/nulo (1,4 mi).
- **Renan** (2,68 mi): ~71% Flávio (1,9 mi), ~29% Lula (0,8 mi).
- **Caiado** (2,61 mi): ~56% Flávio (1,46 mi), ~38% Lula (0,98 mi).
- Com todas as cidades, os números mudaram em relação aos que saíram com as cidades apuradas até as 21h (o Renan, por exemplo, foi de ~83% para ~71% Flávio). Isso mostra quanto essa estimativa depende da amostra.
- O que ela **não** consegue ver é quem trocou de lado entre Lula e Flávio. Por isso as linhas "Lula → Lula 100%" e "Flávio → Flávio 100%" são uma suposição do método, não um resultado. Também desconfio do "branco/nulo → 84% Lula", que pode ser viés de agregação.

**A minha previsão, olhando para trás** (`analise/retroativo.py`):
- A previsão nunca deu Flávio: ficou entre 50,45% e 54% a noite toda. Mas **errou sempre para menos**: com 20% a 50% apurado, previa ~1 a 1,3 ponto menos do que deu, ou seja, 1,3 a 1,6 milhão de votos a menos na conta do Lula. Ela só chegou a ±0,5 ponto do final às 20h48, com 73% apurado.
- **De onde veio o erro:** às 20h09 (30% das seções), 2 dos 3,2 milhões de votos de erro na diferença vieram de **São Paulo**, que tinha só 6,9% apurado (previa 42,1% para o Lula e deu 46,2%). Depois vieram Rio (-518 mil), Ceará (-373 mil) e Rio Grande do Sul (-238 mil).
- **O peso de 10% não foi o problema.** Com 2% ou 25%, o erro mudava pouco (média de 0,86 e 0,72 ponto, contra 0,76). O problema estava no "1º turno + ganho da região": o ganho era medido nas primeiras seções, que não são parecidas com as últimas.
- **O método que teria funcionado:** comparar cada estado com ele mesmo **no mesmo % apurado do 1º turno** e somar essa diferença ao 1º turno final do estado. Ele erra de +0,2 a +0,4 ponto desde os 20% (às 19h57, quando o placar ainda mostrava o Flávio na frente) e tem erro médio de 0,46 ponto, contra 0,76 do meu modelo. Ele não tem nenhum parâmetro para ajustar, o que é bom, mas eu testei depois de saber o resultado e numa noite só. Para confiar nele, preciso testar no 1º turno de 2026 com 2022 e nos turnos de 2022 com 2018.

## Meus palpites (19h16, antes do resultado)

1. **Lula ganha, com uma margem extremamente apertada.** Em 2022 foi um sufoco (Lula 50,90% x Bolsonaro 49,10%, diferença de 1,80 ponto ou 2,14 milhões de votos). Acho que vai ser parecido, mas com a diferença menor ainda.
2. **A abstenção vai ser maior ainda.** Referências: 20,58% no 2º turno de 2022 e 21,08% no 1º turno de 2026.

Para comparar: em 2018, Bolsonaro fez 55,13% x Haddad 44,87%, uma diferença de 10,26 pontos (10,76 milhões de votos).

Os palpites também estão em `dados/palpites.csv`.

3. **20h14, com 34,45% apurado:** **Lula 50,2% x Flávio 49,8%**, uma diferença de 0,4 ponto, coerente com o palpite das 19h16 e igual ao placar de Minas em 2022. Falei "51,2 x 49,8" (soma 101%) e corrigi o Lula para 50,2 às 20h15. E mudei o palpite da abstenção: vai ser **igual à de 2022** (20,58%).
