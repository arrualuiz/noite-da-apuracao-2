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

## Meus palpites (19h16, antes do resultado)

1. **Lula ganha, com uma margem extremamente apertada.** Em 2022 foi um sufoco (Lula 50,90% x Bolsonaro 49,10%, diferença de 1,80 ponto ou 2,14 milhões de votos). Acho que vai ser parecido, mas com a diferença menor ainda.
2. **A abstenção vai ser maior ainda.** Referências: 20,58% no 2º turno de 2022 e 21,08% no 1º turno de 2026.

Para comparar: em 2018, Bolsonaro fez 55,13% x Haddad 44,87%, uma diferença de 10,26 pontos (10,76 milhões de votos).

Os palpites também estão em `dados/palpites.csv`.

3. **20h14, com 34,45% apurado:** **Lula 50,2% x Flávio 49,8%**, uma diferença de 0,4 ponto, coerente com o palpite das 19h16 e igual ao placar de Minas em 2022. Falei "51,2 x 49,8" (soma 101%) e corrigi o Lula para 50,2 às 20h15. E mudei o palpite da abstenção: vai ser **igual à de 2022** (20,58%).
