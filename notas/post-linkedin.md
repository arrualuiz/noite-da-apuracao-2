# Rascunho do post do LinkedIn

Para acompanhar as imagens: o mapa de Curitiba por bairro (painel/curitiba.html), o gráfico "a minha previsão
olhando para trás" (painel/depois.html#previsao) e o mapa das ilhas (painel/depois.html#ilhas).

---

Na noite do 2º turno, eu não fiquei só olhando a apuração: eu tentei prever o resultado. E depois fui medir onde errei.

Montei um coletor em Python que lia os dados do TSE a cada minuto, um modelo de previsão estado por estado e um painel com a minha expectativa contra a apuração real. Antes do primeiro número, registrei os meus palpites.

O que aconteceu:

📈 A previsão apontou o vencedor a noite toda, inclusive quando o placar mostrava o outro candidato na frente (de 17% a 48% apurado).

📉 Mas ela errou sempre para o mesmo lado. Com 20% a 50% apurado, previa ~1 ponto a menos para o vencedor, o equivalente a 1,2 a 1,6 milhão de votos. Fui atrás da causa: 2 dos 3,2 milhões de votos de erro vinham de São Paulo, que apura tarde e não se parece com as primeiras seções.

🔁 Testei, olhando para trás, outro método: comparar cada estado com ele mesmo no mesmo ponto da apuração do 1º turno. O erro médio caiu de 0,76 para 0,46 ponto, sem nenhum parâmetro ajustado. A ressalva: foi uma noite só, e preciso testar em outras eleições antes de confiar.

🗺️ Depois desci ao detalhe: li o boletim de cada uma das 4.056 urnas de Curitiba (formato binário ASN.1, decodificado à mão) e cruzei com o mapa oficial dos 75 bairros. No caminho, achei 680 seções em que o bairro do cadastro não era o bairro real da escola.

🏝️ E procurei as "ilhas": cidades que votam muito diferente das 10 vizinhas. Terras indígenas, cidades universitárias, polos do agronegócio e colônias europeias aparecem sozinhos no mapa.

O que eu levo disso: um modelo que acerta o vencedor e erra a margem com viés não está "certo". Medir o erro, achar a causa e propor uma correção vale mais que acertar por sorte.

Tudo aberto, com código, dados e o diário da noite hora a hora:
👉 https://arrualuiz.github.io/noite-da-apuracao-2/

Próximos passos: refazer a análise em R/Quarto e montar o pipeline em Databricks.

#dados #analisededados #python #eleicoes2026 #dataviz #estatistica
