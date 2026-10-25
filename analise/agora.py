#!/usr/bin/env python3
"""Onde ainda falta apurar e como o Lula está em cada lugar, na última coleta.

Para cada grupo (SP, RJ, MG, Nordeste, ...) mostra quanto já foi apurado, quantos eleitores faltam,
o % do Lula entre Lula e Flávio agora, no mesmo ponto da apuração do 1º turno e no fim do 1º turno.

Uso: python3 analise/agora.py
"""
import csv
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "dados"
BRUTOS_1T = RAIZ.parent / "xx-noite-do-primeiro-turno-2026" / "dados" / "brutos"
GRUPOS = {
    "São Paulo": ["SP"], "Rio de Janeiro": ["RJ"], "Minas Gerais": ["MG"], "Espírito Santo": ["ES"],
    "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Sul": ["PR", "RS", "SC"], "Norte": ["AC", "AM", "AP", "PA", "RO", "RR", "TO"],
    "Centro-Oeste": ["DF", "GO", "MS", "MT"], "Exterior": ["ZZ"],
}


def ler(pasta, uf):
    u = json.loads((pasta / f"{uf.lower()}-u.json").read_text(encoding="utf-8"))
    c = {x["n"]: int(x["vap"]) for a in u["carg"][0]["agr"] for p in a["par"] for x in p["cand"]}
    return {"l": c.get("13", 0), "f": c.get("22", 0), "te": int(u["e"]["te"]), "est": int(u["e"]["est"])}


def grupo(pasta, ufs):
    xs = [ler(pasta, uf) for uf in ufs]
    s = {k: sum(x[k] for x in xs) for k in ("l", "f", "te", "est")}
    s["apurado"] = s["est"] / s["te"] * 100
    s["lula"] = s["l"] / (s["l"] + s["f"]) * 100 if s["l"] + s["f"] else None
    return s


def coletas(brutos):
    return sorted(d for d in brutos.iterdir() if (d / "br-u.json").exists()) if brutos.exists() else []


def mesmo_ponto_1t(ufs, apurado, lista_1t):
    """% do Lula no 1º turno quando o grupo tinha o apurado mais próximo do de agora."""
    melhor = None
    for pasta in lista_1t:
        try:
            g = grupo(pasta, ufs)
        except (OSError, KeyError, ValueError):
            continue
        if g["lula"] is not None and (melhor is None or abs(g["apurado"] - apurado) < abs(melhor["apurado"] - apurado)):
            melhor = g
    return melhor


def main():
    ultima = coletas(PASTA / "brutos")[-1]
    t1 = {r["uf"]: r for r in csv.DictReader((PASTA / "historico" / "2026-t1-uf.csv").open(encoding="utf-8"))}
    lista_1t = coletas(BRUTOS_1T)
    prev = list(csv.DictReader((PASTA / "previsao.csv").open(encoding="utf-8")))[-1]
    br = grupo(ultima, [uf for ufs in GRUPOS.values() for uf in ufs])
    faltam_total = br["te"] - br["est"]

    print(f"Coleta {ultima.name[9:11]}:{ultima.name[11:13]} · {float(prev['secoes_pct']):.2f}% das seções")
    print(f"Placar: Lula {br['lula']:.2f}% x Flávio {100 - br['lula']:.2f}%   ·   "
          f"previsão para 100%: Lula {float(prev['prev_pct_lula']):.2f}%")
    print()
    print(f"{'':16}{'apurado':>8}{'faltam':>10}{'do que':>8}{'Lula':>7}{'Lula 1º':>9}{'Lula 1º':>9}")
    print(f"{'':16}{'':>8}{'(eleit.)':>10}{'falta':>8}{'agora':>7}{'mesmo pt':>9}{'final':>9}")
    for nome, ufs in GRUPOS.items():
        g = grupo(ultima, ufs)
        faltam = g["te"] - g["est"]
        l1, f1 = sum(int(t1[u]["lula"]) for u in ufs), sum(int(t1[u]["flavio"]) for u in ufs)
        m = mesmo_ponto_1t(ufs, g["apurado"], lista_1t) if lista_1t else None
        mesmo = f"{m['lula']:8.1f}%" if m else f"{'–':>9}"
        agora = f"{g['lula']:6.1f}%" if g["lula"] is not None else f"{'–':>7}"
        print(f"{nome:16}{g['apurado']:7.1f}%{faltam / 1e6:8.1f} mi{faltam / faltam_total * 100:7.0f}%"
              f"{agora}{mesmo}{l1 / (l1 + f1) * 100:8.1f}%")
    print()
    print("Lula = % entre Lula e Flávio. \"Mesmo pt\" = o 1º turno quando o lugar tinha o mesmo % apurado de agora.")
    print("\"Do que falta\" = parte dos eleitores ainda não apurados que está naquele lugar.")


if __name__ == "__main__":
    main()
