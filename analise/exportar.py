#!/usr/bin/env python3
"""Exporta o banco para tabelas prontas para R, Python, Power BI, Power Automate, Excel e Sheets.

Uso: python3 analise/exportar.py   (o coletar.py chama a cada coleta)

Saída em dados/export/ (CSV UTF-8 com BOM, separador vírgula, decimal ponto):
  coletas.csv     dimensão: uma linha por coleta
  ufs.csv         dimensão: UF, nome, região
  candidatos.csv  dimensão: número, nome, partido
  apuracao.csv    fato: coleta × abrangência (BR oficial + UFs): seções, eleitorado, válidos…
  votos.csv       fato: coleta × UF × candidato (formato longo, já com nomes e região)
  nacional.csv    coleta: placar nacional pela soma das UFs, diferença e projeção por estado
  lotes.csv       entre coletas consecutivas × abrangência (BR-soma e UFs): votos novos e margem do lote
E também site/dados.js (window.DADOS) para o site de rolagem.
"""
import csv
import json
import sqlite3
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BANCO = RAIZ / "dados" / "apuracao.sqlite"
SAIDA = RAIZ / "dados" / "export"
SITE = RAIZ / "site" / "dados.js"


def escrever(nome, colunas, linhas):
    with (SAIDA / nome).open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(colunas)
        w.writerows(linhas)


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(BANCO)
    q = lambda sql, *a: con.execute(sql, a).fetchall()

    # dimensões e fatos diretos
    escrever("coletas.csv", ["coleta_id", "horario", "versao_tse_br"], q("SELECT * FROM coletas ORDER BY coleta_id"))
    escrever("ufs.csv", ["uf", "nome", "regiao"], q("SELECT * FROM ufs ORDER BY uf"))
    escrever("candidatos.csv", ["numero", "nome", "partido"], q("SELECT * FROM candidatos ORDER BY numero"))
    cols_ap = [r[1] for r in q("PRAGMA table_info(apuracao)")]
    escrever("apuracao.csv", cols_ap, q("SELECT * FROM apuracao ORDER BY coleta_id, abrangencia"))
    escrever("votos.csv",
             ["horario", "coleta_id", "uf", "nome_uf", "regiao", "numero", "candidato", "partido", "votos", "pct_validos"],
             q("""SELECT horario, coleta_id, abrangencia, nome_uf, regiao, numero, candidato, partido, votos, pct_validos
                  FROM v_votos WHERE abrangencia <> 'BR' ORDER BY coleta_id, abrangencia, numero"""))

    # por coleta e UF: votos de Flávio/Lula, válidos e fração apurada
    base = {}
    for cid, uf, vv, el, ea, st, ts in q("""SELECT coleta_id, abrangencia, validos, eleitorado, eleitorado_apurado,
                                            secoes_apuradas, secoes_total FROM apuracao WHERE abrangencia <> 'BR'"""):
        base[(cid, uf)] = {"vv": vv, "frac": ea / el if el else 0, "st": st, "ts": ts, "f": 0, "l": 0}
    for cid, uf, num, v in q("SELECT coleta_id, abrangencia, numero, votos FROM votos WHERE abrangencia <> 'BR' AND numero IN (13, 22)"):
        base[(cid, uf)]["f" if num == 22 else "l"] = v

    coletas = [r[0] for r in q("SELECT coleta_id FROM coletas ORDER BY coleta_id")]
    horario = dict(q("SELECT coleta_id, horario FROM coletas"))
    ufs = sorted({uf for (_, uf) in base})

    nacional, serie = [], []
    for cid in coletas:
        regs = [base[(cid, uf)] for uf in ufs if (cid, uf) in base]
        vv = sum(r["vv"] for r in regs); f = sum(r["f"] for r in regs); l = sum(r["l"] for r in regs)
        sec = sum(r["st"] for r in regs) / sum(r["ts"] for r in regs) * 100
        pf = pl = pv = 0.0
        for r in regs:
            if r["frac"] > 0 and r["vv"]:
                pf += r["f"] / r["frac"]; pl += r["l"] / r["frac"]; pv += r["vv"] / r["frac"]
        linha = [horario[cid], cid, round(sec, 3), vv, f, l, round(f / vv * 100, 3), round(l / vv * 100, 3),
                 f - l, round((f - l) / vv * 100, 3), round(pf / pv * 100, 3), round(pl / pv * 100, 3)]
        nacional.append(linha)
        serie.append({"h": horario[cid][11:16], "dt": horario[cid][:16], "secoes": linha[2], "flavio": linha[6], "lula": linha[7],
                      "proj_flavio": linha[10], "proj_lula": linha[11], "dif_votos": f - l})
    escrever("nacional.csv", ["horario", "coleta_id", "secoes_pct", "validos", "votos_flavio", "votos_lula",
                              "pct_flavio", "pct_lula", "dif_votos", "dif_pp", "proj_flavio", "proj_lula"], nacional)

    lotes = []
    for a, b in zip(coletas, coletas[1:]):
        for uf in ["BR", *ufs]:
            if uf == "BR":
                x = {k: sum(base[(a, u)][k] for u in ufs) for k in ("vv", "f", "l")}
                y = {k: sum(base[(b, u)][k] for u in ufs) for k in ("vv", "f", "l")}
            else:
                x, y = base.get((a, uf)), base.get((b, uf))
                if not x or not y:
                    continue
            dv, df, dl = y["vv"] - x["vv"], y["f"] - x["f"], y["l"] - x["l"]
            if dv <= 0:
                continue
            lotes.append([horario[a], horario[b], uf, dv, df, dl, dv - df - dl, df - dl,
                          round(df / dv * 100, 3), round(dl / dv * 100, 3),
                          round((x["f"] - x["l"]) / x["vv"] * 100, 3) if x["vv"] else None])
    escrever("lotes.csv", ["de", "ate", "abrangencia", "validos_novos", "novos_flavio", "novos_lula", "novos_outros",
                           "saldo_flavio_menos_lula", "pct_lote_flavio", "pct_lote_lula", "margem_acumulada_antes_pp"], lotes)

    # site: série nacional + lotes nacionais
    SITE.parent.mkdir(exist_ok=True)
    lotes_br = [{"de": l[0][11:16], "ate": l[1][11:16], "validos": l[3], "saldo": l[7], "pf": l[8], "pl": l[9]}
                for l in lotes if l[2] == "BR"]
    # leituras feitas à mão antes da coleta automática (prints dos sites), para o início do gráfico do site
    manual = [{"h": r["horario"][11:16], "dt": r["horario"][:16], "secoes": float(r["urnas_pct"]),
               "flavio": float(r["flavio_pct"]), "lula": float(r["lula_pct"]), "fonte": r["nota"].split(";")[0]}
              for r in csv.DictReader(open(RAIZ / "dados" / "snapshots.csv", encoding="utf-8"))
              if not r["nota"].startswith("TSE")]
    SITE.write_text("// gerado por analise/exportar.py — não editar à mão\nwindow.DADOS = "
                    + json.dumps({"serie": serie, "manual": manual, "lotes": lotes_br}, ensure_ascii=False) + ";\n",
                    encoding="utf-8")
    con.close()
    exportar_cases()
    print(f"exportar: {len(coletas)} coletas → dados/export/ (7 CSVs), site/dados.js e site/cases.js")


def exportar_cases():
    """cases/*.md → site/cases.js (window.CASES), para o site abrir sem servidor."""
    cases = []
    for arq in sorted((RAIZ / "cases").glob("[0-9][0-9]-*.md")):
        texto = arq.read_text(encoding="utf-8")
        meta, corpo = {}, texto
        if texto.startswith("---"):
            _, cab, corpo = texto.split("---", 2)
            for linha in cab.strip().splitlines():
                if ":" in linha:
                    k, v = linha.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"')
        corpo = corpo.replace("](graficos/", "](../cases/graficos/")  # no site, o caminho parte de site/
        cases.append({**meta, "arquivo": arq.name, "md": corpo.strip()})
    (RAIZ / "site" / "cases.js").write_text("// gerado por analise/exportar.py — não editar à mão\nwindow.CASES = "
                                           + json.dumps(cases, ensure_ascii=False) + ";\n", encoding="utf-8")


if __name__ == "__main__":
    main()
