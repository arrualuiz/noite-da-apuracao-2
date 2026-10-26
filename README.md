# Noite da Apuração 2

A noite do 2º turno da eleição para Presidente (25/10/2026), Lula x Flávio Bolsonaro, contada com dados coletados direto da API pública do TSE enquanto a apuração acontecia.

**Resultado: Lula reeleito.** Na versão das 21:09 do TSE, com 97,69% das seções apuradas, o resultado ficou matematicamente definido: Lula 51,74% x Flávio Bolsonaro 48,26%. A virada no placar veio às 20h25, com 48% apurado. Com 99,99% apurado: Lula 51,78% (64,2 milhões) x Flávio 48,22% (59,8 milhões), 4,43 milhões de votos de diferença.

É a continuação do [noite-do-primeiro-turno-2026](https://github.com/arrualuiz/noite-do-primeiro-turno-2026), com o mesmo código e a mesma fonte de dados. Comecei às 19h15, com 2% das seções apuradas.

## Meus palpites (19h16, antes do resultado)

1. **Lula ganha com uma margem extremamente apertada**, menor ainda que a de 2022 (50,90% x 49,10%, diferença de 1,80 ponto).
2. **A abstenção vai ser maior ainda** (2º turno de 2022: 20,58%; 1º turno de 2026: 21,08%).

O registro está em [`dados/palpites.csv`](dados/palpites.csv) e o diário da noite em [`notas/notas.md`](notas/notas.md).

## O que tem aqui

- **Coleta** (`coleta/coletar.py`): a cada 60 s consulta os 29 arquivos de `resultados.tse.jus.br` (27 UFs, exterior e nacional) da eleição 6258, grava o placar nacional, o andamento de cada estado e os candidatos em CSV e SQLite, e baixa a curva de evolução do UOL (2026 e 2022).
- **Painel** (`painel/painel.html`, gerado a cada coleta): placar, evolução 2026 x 2022, projeção por estado e andamento por estado e região.
- **Capital x interior** (`coleta/municipios.py`): a cada coleta, os 39 municípios da Grande SP, o Rio e BH, para separar capital, região metropolitana e interior (`dados/segmentos.csv`).
- **Histórico** (`dados/historico/`): resultados oficiais do TSE de 2002 a 2022 e o resultado final do 1º turno de 2026 por estado (`2026-t1-uf.csv`).

## Rodar

```bash
python3 coleta/coletar.py                            # uma coleta
python3 coleta/coletar.py --a-cada 60 --parar-no-fim # repete até a apuração terminar
python3 analise/agora.py                             # onde falta apurar e o Lula agora x o mesmo ponto do 1º turno
python3 analise/trajetoria.py                        # o caminho provável do placar até 100%
python3 analise/abstencao.py                         # abstenção de todas as cidades nos dois turnos
python3 analise/curiosidades.py                      # números absurdos: empates, extremos, cidades que viraram
python3 analise/transferencia.py                     # em pessoas: quem foi votar e para onde foram os votos do 1º turno
python3 analise/extremos.py                          # mínimos e máximos de cada parâmetro, e quem é cada registro
python3 analise/bairros.py                           # Curitiba por bairro e por escola, pelo boletim de cada urna (outra cidade: uf código nome)
python3 analise/ilhas.py                             # cidades que votaram muito diferente das 10 vizinhas (ilhas)
python3 analise/depois.py                            # a página painel/depois.html com todas as análises depois do resultado, em gráficos
python3 analise/retroativo.py                        # depois do resultado: o erro da previsão em cada momento e de onde ele veio
```

Só usa a biblioteca padrão do Python.

## O site

No ar pelo GitHub Pages: **https://arrualuiz.github.io/noite-da-apuracao-2/**

| Página | Arquivo | De onde vem |
|---|---|---|
| Capa | `index.html` | escrita à mão |
| Curitiba na eleição | `painel/curitiba.html` | `painel/curitiba-template.html` + `analise/depois.py` |
| O Brasil depois da apuração | `painel/depois.html` | `painel/depois-template.html` + `analise/depois.py` |
| O painel da noite | `painel/perguntas.html` | `painel/perguntas-template.html` + `analise/perguntas.py` |

O estilo e as funções comuns de Curitiba e do Brasil ficam em `painel/comum.css` e `painel/comum.js`.

**Para mudar o site:**

```bash
git pull                          # pega o que mudou no GitHub (se editei por lá)
# editar o template, o comum.css/comum.js ou o index.html
python3 analise/depois.py         # refaz curitiba.html e depois.html (perguntas.html: analise/perguntas.py)
# conferir em http://127.0.0.1:5500/ (Live Server do VS Code)
git add -A && git commit -m "o que mudou"
git push                          # o GitHub Pages publica em ~1 minuto
```

Os HTML gerados também vão para o git, porque é deles que o GitHub Pages lê. Os dados vêm dos CSVs em `dados/`, que os scripts de `analise/` refazem.

## A noite, hora a hora

O que fiz na noite, na ordem e com onde ver cada coisa: [`notas/linha-do-tempo.md`](notas/linha-do-tempo.md).

## Próximos passos

O projeto está organizado em sprints no [`PLANO.md`](PLANO.md): a noite, o fechamento, a análise em R, o pipeline em Databricks, o relatório em Fabric/Power BI e o case no LinkedIn. O site (`site/index.html`) ainda conta a noite do 1º turno.
