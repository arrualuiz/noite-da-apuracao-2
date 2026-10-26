#!/usr/bin/env python3
"""Presidente nas capitais, de 2002 a 2026: quanto cada capital votou no PT e no principal rival.

Para entender se Curitiba sempre votou assim ou quando mudou. Lê o votacao_partido_munzona de cada ano
(dados abertos do TSE, só o *_BR.csv, por download parcial, como em analise/historico_tse.py) e soma
por município. 2026 vem das coletas desta noite (1º turno: noite-do-primeiro-turno-2026).

Gera dados/historico/capitais_presidente.csv: ano, turno, uf, cd_tse, municipio, partido, votos.
E mostra Curitiba x Paraná x Brasil, com a posição de Curitiba entre as capitais.

Uso: python3 analise/capitais_historia.py
"""
import csv
import json
import zipfile
from collections import defaultdict
from pathlib import Path

from historico_tse import CDN, ArquivoRemoto, linhas_csv

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "dados"
SAIDA = PASTA / "historico" / "capitais_presidente.csv"
ANOS = [2002, 2006, 2010, 2014, 2018, 2022]  # 1994 e 1998 não têm Presidente por município nos dados abertos
CURITIBA = "75353"


def capitais():
    cfg = json.loads((PASTA / "municipios-6258.json").read_text(encoding="utf-8"))
    return {m["cd"]: (a["cd"].upper(), m["nm"].title()) for a in cfg["abr"] for m in a["mu"] if m.get("c") == "s"}


def ano_tse(ano, caps):
    """Votos de Presidente por turno, partido e capital (e o total do PR e do Brasil)."""
    url = f"{CDN}/votacao_partido_munzona/votacao_partido_munzona_{ano}.zip"
    z = zipfile.ZipFile(ArquivoRemoto(url))
    nome = next(n for n in z.namelist() if n.endswith("_BR.csv"))
    out = defaultdict(int)
    with z.open(nome) as fh:
        somar(linhas_csv(fh), caps, out)
    return out


def somar(linhas, caps, out):
    for r in linhas:
        if r["CD_CARGO"] != "1":
            continue
        v = int(r.get("QT_VOTOS_NOMINAIS_VALIDOS") or r.get("QT_VOTOS_NOMINAIS") or 0)
        t, p, cd = int(r["NR_TURNO"]), r["SG_PARTIDO"], r["CD_MUNICIPIO"].zfill(5)
        out[(t, "BR", "BR", "Brasil", p)] += v
        if r["SG_UF"] == "PR":
            out[(t, "PR", "PR", "Paraná", p)] += v
        if cd in caps:
            out[(t, caps[cd][0], cd, caps[cd][1], p)] += v


def ano_2026(caps):
    """2026 das coletas: 1º turno (projeto do 1º turno) e 2º turno (esta noite), Lula = PT, Flávio = PL."""
    out = {}
    pastas = {1: sorted((RAIZ.parent / "xx-noite-do-primeiro-turno-2026" / "dados" / "brutos").glob("*/br-u.json"))[-1].parent,
              2: sorted((PASTA / "brutos").glob("*/br-u.json"))[-1].parent}
    mun = {1: PASTA / "historico" / "tse" / "1t-municipios",
           2: max((d / "todos-mun" for d in (PASTA / "brutos").iterdir() if (d / "todos-mun").exists()), key=lambda p: p.parent.name)}
    partido = {"13": "PT", "22": "PL", "70": "OUTROS", "14": "OUTROS", "55": "OUTROS"}
    for t in (1, 2):
        arquivos = [("BR", "BR", "Brasil", pastas[t] / "br-u.json"), ("PR", "PR", "Paraná", pastas[t] / "pr-u.json")]
        arquivos += [(uf, cd, nm, mun[t] / f"{uf.lower()}{cd}.json") for cd, (uf, nm) in caps.items()]
        for uf, cd, nm, arq in arquivos:
            if not arq.exists():
                continue
            u = json.loads(arq.read_text(encoding="utf-8"))
            for a in u["carg"][0]["agr"]:
                for p in a["par"]:
                    for c in p["cand"]:
                        k = (t, uf, cd, nm, partido.get(c["n"], "OUTROS"))
                        out[k] = out.get(k, 0) + int(c["vap"])
    return out


def main():
    caps = capitais()
    linhas = []
    for ano in ANOS:
        for (t, uf, cd, nm, p), v in sorted(ano_tse(ano, caps).items()):
            linhas.append([ano, t, uf, cd, nm, p, v])
        print(f"{ano} lido")
    for (t, uf, cd, nm, p), v in sorted(ano_2026(caps).items()):
        linhas.append([2026, t, uf, cd, nm, p, v])
    with SAIDA.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ano", "turno", "uf", "cd_tse", "municipio", "partido", "votos"])
        w.writerows(linhas)

    # Curitiba x Paraná x Brasil: PT no 1º turno e, no 2º, PT entre os dois
    v = defaultdict(lambda: defaultdict(int))
    for ano, t, uf, cd, nm, p, n in linhas:
        v[(ano, t, cd)][p] += n
    print(f"\n{'':6}{'PT no 1º turno':>34}   {'PT no 2º turno (entre os dois)':>40}   Curitiba entre as 27 capitais")
    print(f"{'':6}{'Curitiba':>12}{'Paraná':>11}{'Brasil':>11}   {'Curitiba':>12}{'Paraná':>11}{'Brasil':>11}{'':6}   (1 = a que menos votou no PT)")
    for ano in ANOS + [2026]:
        def pt(t, cd):
            x = v.get((ano, t, cd))
            if not x:
                return None
            tot = sum(x.values()) if t == 1 else x["PT"] + max(n for p, n in x.items() if p != "PT")
            return x["PT"] / tot * 100
        t2 = (ano, 2, "BR") in v
        ranking = sorted((pt(2 if t2 else 1, cd), cd) for cd in caps if pt(2 if t2 else 1, cd) is not None)
        pos = [cd for _, cd in ranking].index(CURITIBA) + 1
        f = lambda x: f"{x:11.1f}%" if x is not None else f"{'–':>12}"
        print(f"{ano:<6}{f(pt(1, CURITIBA))}{f(pt(1, 'PR'))[1:]}{f(pt(1, 'BR'))[1:]}   "
              f"{f(pt(2, CURITIBA)) if t2 else f(None)}{(f(pt(2, 'PR')) if t2 else f(None))[1:]}{(f(pt(2, 'BR')) if t2 else f(None))[1:]}"
              f"{'':6}   {pos}ª de {len(ranking)} ({'2º' if t2 else '1º'} turno)")
    print(f"\nGravado em {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
