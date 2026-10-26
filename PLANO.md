# Plano em sprints

Agora o foco é a noite inteira: os dados guardados, os painéis e a previsão. As sprints 1 a 5 ficam para depois.

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

## Sprint 0 · A noite (25/10, 19h15 até o fim da apuração) ▶️

- [x] ⚙️ Coletor do 1º turno apontado para o 2º (TSE 6258), uma coleta por minuto, PC sem suspender
- [x] 🙋 Palpites registrados às 19h16 (`dados/palpites.csv`)
- [x] ⚙️ Repositório git local, README e diário da noite (`notas/notas.md`)
- [x] 🙋 Repositório público no GitHub: https://github.com/arrualuiz/noite-da-apuracao-2 (19h55)
- [x] ⚙️ Coletor religado com `--git`: envia os dados ao GitHub a cada 30 min e no fim
- [x] ⚙️ Painel das perguntas (`painel/perguntas.html`) e previsão do resultado final (`analise/perguntas.py`, `dados/previsao.csv`), recalculados a cada coleta
- [ ] ⚙️ Anotar no diário os marcos da noite: virada (se houver), resultado matematicamente definido e 100%

## Sprint 1 · Fechar a noite (26 e 27/10)

- [x] ⚙️ Conferir os palpites com o resultado final (em `notas/notas.md`, com 99,99% apurado)
- [x] ⚙️ Olhar para trás: o erro da previsão em cada momento e de onde veio (`analise/retroativo.py`: o modelo previu menos Lula a noite toda, por causa de SP; o método "mesmo ponto do 1º turno" errava menos)
- [ ] ⚙️ Testar o método "mesmo ponto" em outras noites (1º turno de 2026 contra 2022), para ver se não foi sorte de uma noite só
- [ ] ⚙️ Entender por que a abstenção subiu no Norte (Amapá, Pará, Acre e Amazonas) quando caiu no resto do país
- [ ] ⚙️ Fechar o case 17 do 1º turno: o Lula precisava de ~65% dos outros, quanto ele levou?
- [ ] ⚙️ Adaptar o painel para o 2º turno (hoje ele ainda tem textos do 1º)
- [ ] ⚙️ README e CONTEXTO com a linha do tempo da noite

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
