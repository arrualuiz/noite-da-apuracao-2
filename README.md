# Noite da Apuração 2

A noite do 2º turno da eleição para Presidente (25/10/2026), Lula x Flávio Bolsonaro, contada com dados coletados direto da API pública do TSE enquanto a apuração acontecia.

É a continuação do [noite-do-primeiro-turno-2026](https://github.com/arrualuiz/noite-do-primeiro-turno-2026), com o mesmo código e a mesma fonte de dados. Comecei às 19h15, com 2% das seções apuradas.

## Meus palpites (19h16, antes do resultado)

1. **Lula ganha com uma margem extremamente apertada**, menor ainda que a de 2022 (50,90% x 49,10%, diferença de 1,80 ponto).
2. **A abstenção vai ser maior ainda** (2º turno de 2022: 20,58%; 1º turno de 2026: 21,08%).

O registro está em [`dados/palpites.csv`](dados/palpites.csv) e o diário da noite em [`notas/notas.md`](notas/notas.md).

## O que tem aqui

- **Coleta** (`coleta/coletar.py`): a cada 60 s consulta os 29 arquivos de `resultados.tse.jus.br` (27 UFs, exterior e nacional) da eleição 6258, grava o placar nacional, o andamento de cada estado e os candidatos em CSV e SQLite, e baixa a curva de evolução do UOL (2026 e 2022).
- **Painel** (`painel/painel.html`, gerado a cada coleta): placar, evolução 2026 x 2022, projeção por estado e andamento por estado e região.
- **Histórico** (`dados/historico/`): resultados oficiais do TSE de 2002 a 2022 e o resultado final do 1º turno de 2026 por estado (`2026-t1-uf.csv`).

## Rodar

```bash
python3 coleta/coletar.py                            # uma coleta
python3 coleta/coletar.py --a-cada 60 --parar-no-fim # repete até a apuração terminar
```

Só usa a biblioteca padrão do Python.

## Ainda falta

- Adaptar o painel e o site (`site/index.html` ainda conta a noite do 1º turno) para o 2º turno.
- Comparar a curva desta noite com as de 2018, 2022 e do 1º turno de 2026.
- Conferir os palpites com o resultado final.
