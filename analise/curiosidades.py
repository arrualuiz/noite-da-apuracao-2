#!/usr/bin/env python3
"""Números absurdos da noite: os extremos das cidades, de Minas e da velocidade da apuração.

Usa os arquivos de todos os municípios baixados por analise/abstencao.py (2º turno, na última
vez que ele rodou) e os do 1º turno. Só entram nos extremos as cidades 100% apuradas.

Uso: python3 analise/abstencao.py && python3 analise/curiosidades.py
"""
import csv
import json
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "dados"
PASTA_1T = PASTA / "historico" / "tse" / "1t-municipios"


def mil(n):
    return f"{n:,.0f}".replace(",", ".")


def votos(arq):
    u = json.loads(arq.read_text(encoding="utf-8"))
    c = {x["n"]: int(x["vap"]) for a in u["carg"][0]["agr"] for p in a["par"] for x in p["cand"]}
    e = u["e"]
    return {"l": c.get("13", 0), "f": c.get("22", 0), "te": int(e["te"]), "est": int(e["est"]),
            "c": int(e["c"]), "a": int(e["a"]), "vv": int(u["v"]["vv"])}


def main():
    pasta_2t = max((d / "todos-mun" for d in (PASTA / "brutos").iterdir() if (d / "todos-mun").exists()),
                   key=lambda p: p.parent.name)
    cfg = json.loads((PASTA / "municipios-6258.json").read_text(encoding="utf-8"))
    cidades = []
    for a in cfg["abr"]:
        for m in a["mu"]:
            uf, cd = a["cd"], m["cd"]
            a2, a1 = pasta_2t / f"{uf}{cd}.json", PASTA_1T / f"{uf}{cd}.json"
            if not (a2.exists() and a1.exists()):
                continue
            x, y = votos(a2), votos(a1)
            if x["est"] < x["te"] or x["l"] + x["f"] == 0 or y["l"] + y["f"] == 0:
                continue
            cidades.append({"nome": f"{m['nm'].title()} ({uf.upper()})", "uf": uf.upper(), **x,
                            "l1": y["l"], "f1": y["f"], "pl": x["l"] / (x["l"] + x["f"]) * 100,
                            "pl1": y["l"] / (y["l"] + y["f"]) * 100})
    br = [c for c in cidades if c["uf"] != "ZZ"]
    hora = pasta_2t.parent.name
    print(f"NÚMEROS ABSURDOS · cidades 100% apuradas às {hora[9:11]}:{hora[11:13]}: {len(br)} no Brasil\n")

    print("1. Empates e quase empates (diferença entre Lula e Flávio, em votos)")
    for c in sorted(br, key=lambda c: abs(c["l"] - c["f"]))[:8]:
        print(f"   {c['nome']:34} Lula {mil(c['l']):>7} x Flávio {mil(c['f']):>7}  → diferença de {abs(c['l'] - c['f'])}")

    print("\n2. As cidades mais de um lado só (% entre Lula e Flávio)")
    for c in sorted(br, key=lambda c: -c["pl"])[:4]:
        print(f"   {c['nome']:34} Lula {c['pl']:5.1f}%  ({mil(c['l'])} x {mil(c['f'])})")
    for c in sorted(br, key=lambda c: c["pl"])[:4]:
        print(f"   {c['nome']:34} Flávio {100 - c['pl']:5.1f}%  ({mil(c['f'])} x {mil(c['l'])})")

    print("\n3. Quem mais mudou do 1º para o 2º turno (pontos do Lula; cidades com 10 mil eleitores ou mais)")
    medias = [c for c in br if c["te"] >= 10_000]
    for c in sorted(medias, key=lambda c: -(c["pl"] - c["pl1"]))[:5]:
        print(f"   {c['nome']:34} {c['pl1']:5.1f}% → {c['pl']:5.1f}%  ({c['pl'] - c['pl1']:+.1f})")
    for c in sorted(medias, key=lambda c: c["pl"] - c["pl1"])[:3]:
        print(f"   {c['nome']:34} {c['pl1']:5.1f}% → {c['pl']:5.1f}%  ({c['pl'] - c['pl1']:+.1f})")

    viraram = [c for c in br if (c["pl"] - 50) * (c["pl1"] - 50) < 0]
    p_l = sum(1 for c in viraram if c["pl"] > 50)
    print(f"\n4. Cidades que mudaram de lado do 1º para o 2º turno: {len(viraram)} "
          f"({p_l} para o Lula, {len(viraram) - p_l} para o Flávio)")
    for c in sorted(viraram, key=lambda c: -c["te"])[:5]:
        print(f"   {c['nome']:34} {c['pl1']:5.1f}% → {c['pl']:5.1f}%  ({mil(c['te'])} eleitores)")

    print("\n5. As maiores vantagens em votos")
    for c in sorted(cidades, key=lambda c: -(c["l"] - c["f"]))[:3]:
        print(f"   {c['nome']:34} Lula por {mil(c['l'] - c['f'])}")
    for c in sorted(cidades, key=lambda c: c["l"] - c["f"])[:3]:
        print(f"   {c['nome']:34} Flávio por {mil(c['f'] - c['l'])}")

    print("\n6. A menor cidade e a maior (eleitores)")
    for c in (min(br, key=lambda c: c["te"]), max(cidades, key=lambda c: c["te"])):
        print(f"   {c['nome']:34} {mil(c['te'])} eleitores · Lula {mil(c['l'])} x Flávio {mil(c['f'])} · abstenção {mil(c['a'])}")

    # Minas e a velocidade da apuração (do coletor)
    prev = list(csv.DictReader((PASTA / "previsao.csv").open(encoding="utf-8")))
    ufs = {r["uf"]: r for r in csv.DictReader((PASTA / "perguntas_uf.csv").open(encoding="utf-8"))}
    mg = ufs["MG"]
    dif_mg = int(mg["lula"]) - int(mg["flavio"])
    print(f"\n7. Minas: Lula {mil(int(mg['lula']))} x Flávio {mil(int(mg['flavio']))} ({float(mg['apurado']):.1f}% apurado)"
          f" → diferença de {mil(abs(dif_mg))} votos para o {'Lula' if dif_mg > 0 else 'Flávio'}")
    print(f"   É {abs(dif_mg) / int(mg['lula']) * 100:.2f}% dos votos do Lula em Minas. Em 2022 foram 49.650.")
    trocas, lider = 0, None
    for r in prev:
        if r["mg_pct_lula"]:
            q = float(r["mg_pct_lula"]) > 50
            trocas += lider is not None and q != lider
            lider = q
    print(f"   Trocas de liderança em Minas durante a noite: {trocas}")

    snaps = list(csv.DictReader((PASTA / "export" / "nacional.csv").open(encoding="utf-8-sig")))
    maior = (0, None)
    for a, b in zip(snaps, snaps[1:]):
        t = (datetime.fromisoformat(b["horario"]) - datetime.fromisoformat(a["horario"])).total_seconds()
        if t > 0:
            v = (int(b["validos"]) - int(a["validos"])) / t
            maior = max(maior, (v, b["horario"]))
    print(f"\n8. Velocidade máxima da apuração: {mil(maior[0])} votos válidos por segundo (perto das {maior[1][11:16]})"
          f" = {mil(maior[0] * 60)} por minuto")
    ult = snaps[-1]
    print(f"   Votos válidos já contados: {mil(int(ult['validos']))} · diferença Lula x Flávio agora: {mil(abs(int(ult['dif_votos'])))}")


if __name__ == "__main__":
    main()
