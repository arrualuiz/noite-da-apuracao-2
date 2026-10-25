# Plano em sprints

Objetivo: transformar a noite do 2º turno num case de **análise de dados** para o LinkedIn, mostrando o caminho completo: coleta, banco, análise em R, pipeline em Databricks e relatório em Fabric/Power BI. A ideia é que uma empresa de dados olhe e veja que eu sei trabalhar com dados de ponta a ponta.

**Legenda:** 🙋 eu faço/decido · ⚙️ trabalho técnico · ▶️ em andamento · ✅ feito

## A pergunta do case

Um case bom responde a uma pergunta. A minha proposta:

> **Para onde foram os votos de quem não votou em Lula nem em Flávio no 1º turno?**

No 1º turno, o case 17 calculou que o Lula precisava de ~65% desses votos para empatar. Hoje dá para medir quanto ele levou: estado por estado ao vivo e, depois, município por município, com os dados abertos do TSE. Essa pergunta atravessa todas as sprints.

- [ ] 🙋 Confirmar ou trocar a pergunta do case

## Sprint 0 · A noite (25/10, 19h15 até o fim da apuração) ▶️

- [x] ⚙️ Coletor do 1º turno apontado para o 2º (TSE 6258), uma coleta por minuto, PC sem suspender
- [x] 🙋 Palpites registrados às 19h16 (`dados/palpites.csv`)
- [x] ⚙️ Repositório git local, README e diário da noite (`notas/notas.md`)
- [ ] 🙋 Autorizar o repositório público `noite-da-apuracao-2` no GitHub
- [ ] ⚙️ Religar o coletor com `--git`, que envia os dados ao GitHub a cada 30 min
- [ ] ⚙️ Acompanhar ao vivo quanto o Lula ganha sobre o 1º turno em cada estado (a pergunta do case)
- [ ] ⚙️ Anotar no diário os marcos da noite: virada (se houver), resultado matematicamente definido e 100%

## Sprint 1 · Fechar a noite (26 e 27/10)

- [ ] ⚙️ Conferir os palpites com o resultado final
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
