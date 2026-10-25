#!/usr/bin/env python3
"""Abstenção em todas as cidades, no 2º turno (até onde já foi apurado) e no 1º turno.

Baixa do TSE o arquivo de cada um dos ~5.570 municípios (e do exterior):
  - 1º turno (6257): uma vez só, em dados/historico/tse/1t-municipios/
  - 2º turno (6258): a cada vez que roda, em dados/brutos/<última coleta>/todos-mun/
e grava dados/abstencao_municipios.csv, com a abstenção de cada cidade nos dois turnos.

Uso: python3 analise/abstencao.py            # baixa e mostra os exemplos
     python3 analise/abstencao.py --so-ler   # só mostra, com o que já foi baixado
"""
import csv
import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "dados"
BASE = "https://resultados.tse.jus.br/oficial/ele2026/{e}/dados/{uf}/{uf}{cd}-c0001-e00{e}-u.json"
PASTA_1T = PASTA / "historico" / "tse" / "1t-municipios"
SAIDA = PASTA / "abstencao_municipios.csv"


def baixar(url, destino):
    if destino.exists() and destino.stat().st_size > 0:
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            destino.write_bytes(r.read())
        return True
    except Exception:
        return False


def lista_municipios():
    cfg = json.loads((PASTA / "municipios-6258.json").read_text(encoding="utf-8"))
    return [(a["cd"], m["cd"], m["nm"], m.get("c") == "s") for a in cfg["abr"] for m in a["mu"]]


def ler(arq):
    e = json.loads(arq.read_text(encoding="utf-8"))["e"]
    return int(e["te"]), int(e["est"]), int(e["c"]), int(e["a"])


def main():
    muns = lista_municipios()
    coleta = sorted(d for d in (PASTA / "brutos").iterdir() if (d / "br-u.json").exists())[-1]
    pasta_2t = coleta / "todos-mun"
    if "--so-ler" not in sys.argv:
        PASTA_1T.mkdir(parents=True, exist_ok=True)
        pasta_2t.mkdir(exist_ok=True)
        pedidos = [(BASE.format(e="6257", uf=uf, cd=cd), PASTA_1T / f"{uf}{cd}.json") for uf, cd, _, _ in muns]
        pedidos += [(BASE.format(e="6258", uf=uf, cd=cd), pasta_2t / f"{uf}{cd}.json") for uf, cd, _, _ in muns]
        with ThreadPoolExecutor(max_workers=8) as ex:
            ok = sum(ex.map(lambda p: baixar(*p), pedidos))
        print(f"{ok} de {len(pedidos)} arquivos baixados ({coleta.name})")
    else:
        pasta_2t = max((d / "todos-mun" for d in (PASTA / "brutos").iterdir() if (d / "todos-mun").exists()),
                       key=lambda p: p.parent.name)

    linhas = []
    for uf, cd, nome, capital in muns:
        a1, a2 = PASTA_1T / f"{uf}{cd}.json", pasta_2t / f"{uf}{cd}.json"
        if not (a1.exists() and a2.exists()):
            continue
        te1, _, c1, ab1 = ler(a1)
        te, est, c, ab = ler(a2)
        linhas.append({
            "uf": uf.upper(), "cd_tse": cd, "municipio": nome.title(), "capital": int(capital),
            "eleitorado": te, "apurado_pct": round(est / te * 100, 1) if te else 0,
            "comparecimento": c, "abstencao": ab, "pct_abstencao": round(ab / (c + ab) * 100, 2) if c + ab else None,
            "abstencao_1t": ab1, "pct_abstencao_1t": round(ab1 / (c1 + ab1) * 100, 2) if c1 + ab1 else None,
        })
    for l in linhas:
        l["dif_pp"] = round(l["pct_abstencao"] - l["pct_abstencao_1t"], 2) if l["pct_abstencao"] is not None else None
    with SAIDA.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)

    # exemplos: só cidades 100% apuradas, para a taxa valer
    prontas = [l for l in linhas if l["apurado_pct"] >= 100 and l["pct_abstencao"] is not None
               and l["pct_abstencao_1t"] is not None and l["uf"] != "ZZ"]
    exterior = [l for l in linhas if l["uf"] == "ZZ" and l["apurado_pct"] >= 100 and l["pct_abstencao"] is not None]
    print(f"{len(linhas)} cidades lidas · {len(prontas)} já 100% apuradas no 2º turno · {coleta.name[9:11]}:{coleta.name[11:13]}\n")

    def mil(n):
        return f"{n:,}".replace(",", ".")

    def mostrar(titulo, lista):
        print(titulo)
        for l in lista:
            print(f"  {l['municipio'][:28]:28} {l['uf']}  eleitores {mil(l['eleitorado']):>10}  abstenções {mil(l['abstencao']):>9}"
                  f"  {l['pct_abstencao']:5.1f}%  (1º turno {l['pct_abstencao_1t']:5.1f}%; {l['dif_pp']:+.1f} pts)")
        print()

    mostrar("Mais abstenções em número (100% apuradas)", sorted(prontas, key=lambda l: -l["abstencao"])[:8])
    mostrar("Menos abstenções em número (100% apuradas)", sorted(prontas, key=lambda l: l["abstencao"])[:8])
    grandes = [l for l in prontas if l["eleitorado"] >= 50_000]
    mostrar("Maior % de abstenção (100% apuradas, 50 mil eleitores ou mais)", sorted(grandes, key=lambda l: -l["pct_abstencao"])[:8])
    mostrar("Menor % de abstenção (100% apuradas, 50 mil eleitores ou mais)", sorted(grandes, key=lambda l: l["pct_abstencao"])[:8])
    mostrar("Exterior: maior abstenção em número (100% apuradas)", sorted(exterior, key=lambda l: -l["abstencao"])[:5])
    mostrar("Mais subiu do 1º para o 2º turno (pontos; 100% apuradas, 50 mil eleitores ou mais)", sorted(grandes, key=lambda l: -l["dif_pp"])[:8])
    mostrar("Mais caiu do 1º para o 2º turno (pontos; 100% apuradas, 50 mil eleitores ou mais)", sorted(grandes, key=lambda l: l["dif_pp"])[:8])


if __name__ == "__main__":
    main()
