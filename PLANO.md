# Plano em sprints

## Onde parei (26/10, 01h)

A noite acabou (Lula eleito, 100% apurado, coletor desligado) e a Sprint 1 andou quase toda na própria madrugada. Tudo está commitado e no GitHub; o site está no ar em https://arrualuiz.github.io/noite-da-apuracao-2/ (capa, A noite, O Brasil, Curitiba, 1º → 2º turno, com o menu `painel/menu.js` em todas). O painel consolidado `painel/admin.html` fica só no PC (http://127.0.0.1:5500/painel/admin.html).

Para amanhã, na ordem:
1. 🙋 Revisar e publicar o post do LinkedIn (`notas/post-linkedin.md`), com prints do mapa de Curitiba por bairro, dos mini mapas 2002–2026, da previsão olhando para trás e das ilhas.
2. ⚙️ Testar as hipóteses das ilhas com o Censo 2022 (% indígena, já baixável por município) e a área de soja (`analise/municipios.py`).
3. ⚙️ Testar o método "mesmo ponto do 1º turno" no 1º turno de 2026 (contra 2022), para ver se não foi sorte.
4. ⚙️ Por que a abstenção subiu no Norte (Amapá +8 pts).
5. Depois: Sprint 2 (R/Quarto), com os CSVs de `dados/` já prontos.

Como atualizar o site: está no README, seção "O site".

Objetivo: transformar a noite do 2º turno num case de **análise de dados** para o LinkedIn, mostrando o caminho completo: coleta, banco, análise em R, pipeline em Databricks e relatório em Fabric/Power BI. A ideia é que uma empresa de dados olhe e veja que eu sei trabalhar com dados de ponta a ponta.

**Legenda:** 🙋 eu faço/decido · ⚙️ trabalho técnico · ▶️ em andamento · ✅ feito

## As perguntas do case

A lista vai crescendo conforme as dúvidas aparecem. O painel `painel/perguntas.html` responde as que dá para medir durante a noite, e se atualiza a cada coleta.

1. **Para onde foram os votos de quem não votou em Lula nem em Flávio no 1º turno?** Ao vivo, por estado; depois, por município. Não dá para saber com certeza o que cada eleitor fez, só estimar pelo saldo.
2. **Quem ganha Minas?** Meu foco. Em 2022, Minas foi decidida por ~50 mil votos.
3. **Algum estado do Sul mudou de lado entre o 1º e o 2º turno?** Sou do Sul.
4. **Nordeste: o Lula cresceu em votos? E o Flávio?** Votos absolutos, do 1º para o 2º turno.
5. **O comparecimento mudou do 1º para o 2º turno?** Polêmicas sobre transporte público no Sudeste e no Nordeste, e o clima no Sul. Os dados medem a diferença; a causa precisa de outra fonte (notícias, clima por município) e fica para depois.
6. **O Lula cresceu em cada estado? Isso dá para tirar a diferença do 1º turno?** Mapa do ganho do Lula e a virada de cada estado em votos, somada contra a diferença do 1º turno (Flávio +2,22 milhões).

## Sprint 0 · A noite (25/10, 19h15 até o fim da apuração) ✅

- [x] ⚙️ Coletor do 1º turno apontado para o 2º (TSE 6258), uma coleta por minuto, PC sem suspender
- [x] 🙋 Palpites registrados às 19h16 (`dados/palpites.csv`)
- [x] ⚙️ Repositório git local, README e diário da noite (`notas/notas.md`)
- [x] 🙋 Repositório público no GitHub: https://github.com/arrualuiz/noite-da-apuracao-2 (19h55)
- [x] ⚙️ Coletor religado com `--git`: envia os dados ao GitHub a cada 30 min e no fim
- [x] ⚙️ Painel das perguntas (`painel/perguntas.html`) e previsão do resultado final (`analise/perguntas.py`, `dados/previsao.csv`), recalculados a cada coleta
- [x] ⚙️ Anotar no diário os marcos da noite: virada às 20h25, resultado definido às 21h09, 100% e totalização às 23h28 (`notas/notas.md` e `notas/linha-do-tempo.md`)

## Sprint 1 · Fechar a noite (começou na madrugada de 25 para 26/10) ▶️

- [x] ⚙️ Conferir os palpites com o resultado final (em `notas/notas.md`, com 99,99% apurado)
- [x] ⚙️ Olhar para trás: o erro da previsão em cada momento e de onde veio (`analise/retroativo.py`: o modelo previu menos Lula a noite toda, por causa de SP; o método "mesmo ponto do 1º turno" errava menos)
- [ ] ⚙️ Testar o método "mesmo ponto" em outras noites (1º turno de 2026 contra 2022), para ver se não foi sorte de uma noite só
- [ ] ⚙️ Entender por que a abstenção subiu no Norte (Amapá, Pará, Acre e Amazonas) quando caiu no resto do país
- [ ] ⚙️ Testar as hipóteses das ilhas (`dados/ilhas.csv`): a diferença de cada cidade para as vizinhas x % de população indígena (Censo 2022), área de soja e se tem universidade
- [x] 🙋 Publicar as páginas no GitHub Pages: https://arrualuiz.github.io/noite-da-apuracao-2/ (25/10, 23h59)
- [x] ⚙️ Curitiba com a divisa de cada bairro (malha de bairros do IPPUC), pintando o bairro inteiro, e o voto da cidade desde 2002 (`painel/curitiba.html`)
- [ ] ⚙️ Fechar o case 17 do 1º turno: o Lula precisava de ~65% dos outros, quanto ele levou?
- [ ] ⚙️ Adaptar o painel para o 2º turno (hoje ele ainda tem textos do 1º)
- [x] ⚙️ README com a linha do tempo da noite (`notas/linha-do-tempo.md`)
- [ ] 🙋 Revisar e publicar o post do LinkedIn (`notas/post-linkedin.md`), com as imagens do mapa de Curitiba, da previsão e das ilhas
- [x] ⚙️ Testar as hipóteses de Curitiba: renda e cor por bairro (Censo 2022) x voto por bairro, de 2002 a 2026 (`analise/curitiba_historia.py`): até 2014 a renda explicava o voto (r ≈ −0,9); em 2026, quase nada (−0,17). Escolaridade por bairro não existe no Censo (só alfabetização, ~100% em todos)
- [x] ⚙️ Do 1º para o 2º turno em todas as eleições do PT, por estado e capital (`analise/crescimento.py`, `painel/crescimento.html`) e Curitiba eleição a eleição
- [x] ⚙️ Auditoria das contas do TSE (`analise/auditoria.py`): urnas de Curitiba e todos os municípios fecham, sem nenhuma inconsistência
- [x] ⚙️ Ilhas num mapa por município, com zoom no estado e as 10 vizinhas de cada cidade
- [x] ⚙️ Menu em todas as páginas e painel consolidado (admin) só no PC

## Sprint 2 · Análise em R (28/10 a 02/11)

É o centro do case, porque análise de dados é o meu foco.

- [ ] 🙋 Instalar R, tidyverse e Quarto (`sudo apt install r-base r-cran-tidyverse r-cran-rsqlite r-cran-dbi r-cran-sf` e o Quarto pelo site)
- [ ] ⚙️ Baixar o resultado por município dos dois turnos (dados abertos do TSE, 5.570 municípios)
- [ ] ⚙️ Medir a transferência de votos por município: ganho do Lula x votos dos outros candidatos no 1º turno (regressão, com os limites da inferência ecológica explicados)
- [ ] ⚙️ Mapas com `ggplot2` + `sf` e um relatório Quarto publicado no GitHub Pages

## Sprint 3 · Databricks (03 a 09/11)

Mostra engenharia de dados: os JSON brutos de cada coleta, das duas noites, são uma camada bronze pronta.

- [ ] 🙋 Criar conta no Databricks Free Edition
- [ ] ⚙️ Arquitetura medalhão: **bronze** (JSON brutos do TSE), **silver** (tabelas Delta limpas por coleta, UF e candidato), **gold** (placar nacional e por estado minuto a minuto, transferência de votos)
- [ ] ⚙️ Notebooks em PySpark e SQL, um job agendado e um dashboard
- [ ] ⚙️ Exportar os notebooks para a pasta `databricks/` do repositório

## Sprint 4 · Fabric e Power BI (10 a 16/11)

- [ ] 🙋 Ver qual conta usar: o trial do Fabric não aceita e-mail pessoal (Gmail), precisa de conta de trabalho ou de estudante (a da faculdade pode servir)
- [ ] ⚙️ Lakehouse com a camada gold e um relatório Power BI: a noite em gráficos e o mapa da transferência de votos

## Sprint 5 · LinkedIn (17 a 20/11)

- [ ] ⚙️ README como página de portfólio: a pergunta, a arquitetura em uma imagem, os achados e os links
- [ ] 🙋 Post no LinkedIn com 3 ou 4 imagens (curva da noite, mapa, arquitetura) e o link do repositório
- [ ] 🙋 Repositório fixado no GitHub e projeto na seção "Projetos" do LinkedIn
