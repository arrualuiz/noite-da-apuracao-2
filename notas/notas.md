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

## Meus palpites (19h16, antes do resultado)

1. **Lula ganha, com uma margem extremamente apertada.** Em 2022 foi um sufoco (Lula 50,90% x Bolsonaro 49,10%, diferença de 1,80 ponto ou 2,14 milhões de votos). Acho que vai ser parecido, mas com a diferença menor ainda.
2. **A abstenção vai ser maior ainda.** Referências: 20,58% no 2º turno de 2022 e 21,08% no 1º turno de 2026.

Para comparar: em 2018, Bolsonaro fez 55,13% x Haddad 44,87%, uma diferença de 10,26 pontos (10,76 milhões de votos).

Os palpites também estão em `dados/palpites.csv`.

3. **20h14, com 34,45% apurado:** **Lula 50,2% x Flávio 49,8%**, uma diferença de 0,4 ponto, coerente com o palpite das 19h16 e igual ao placar de Minas em 2022. Falei "51,2 x 49,8" (soma 101%) e corrigi o Lula para 50,2 às 20h15. E mudei o palpite da abstenção: vai ser **igual à de 2022** (20,58%).
