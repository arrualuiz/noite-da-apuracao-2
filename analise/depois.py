#!/usr/bin/env python3
"""A página "Depois da apuração": as análises feitas com o resultado final, em gráficos.

Junta os CSVs gerados pelos outros scripts e grava painel/depois.html a partir de
painel/depois-template.html (troca /*DADOS*/null pelo JSON):
  - Curitiba por escola e por bairro      dados/curitiba_secoes.csv, dados/curitiba_bairros.csv (analise/bairros.py)
                                         e o contorno do município, dados/curitiba-contorno.geojson (IBGE, malha
                                         municipal: servicodados.ibge.gov.br/api/v3/malhas/municipios/4106902)
  - ilhas: cidades x vizinhas            dados/ilhas.csv (analise/ilhas.py)
  - a previsão olhando para trás         dados/retroativo.csv (analise/retroativo.py)
  - para onde foram os votos do 1º turno dados/transferencia.csv (analise/transferencia.py)
  - abstenção por estado                 dados/abstencao_municipios.csv (analise/abstencao.py)
  - mínimos e máximos                    dados/extremos.csv (analise/extremos.py)

Uso: python3 analise/depois.py
"""
import csv
import json
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "dados"
TEMPLATE = RAIZ / "painel" / "depois-template.html"
SAIDA = RAIZ / "painel" / "depois.html"
# caixa de Curitiba: fora dela, a coordenada do local de votação está errada no cadastro
CAIXA_CWB = (-25.65, -25.33, -49.40, -49.18)


def ler(nome, enc="utf-8"):
    return list(csv.DictReader((PASTA / nome).open(encoding=enc)))


def num(v):
    try:
        f = float(v)
        return int(f) if f.is_integer() and "." not in v else f
    except (TypeError, ValueError):
        return v


def curitiba():
    escolas, fora = {}, 0
    for s in ler("curitiba_secoes.csv"):
        try:
            lat, lon = float(s["lat"]), float(s["lon"])
        except ValueError:
            lat = lon = None
        e = escolas.setdefault((s["local_votacao"], s["bairro"]), {"nome": s["local_votacao"], "bairro": s["bairro"],
                                                                   "lat": lat, "lon": lon, "secoes": 0})
        e["secoes"] += 1
        for k in ("aptos_2t", "comparecimento_2t", "lula_2t", "flavio_2t", "lula_1t", "flavio_1t", "aptos_1t", "comparecimento_1t"):
            e[k] = e.get(k, 0) + int(s[k])
    lista = []
    for e in escolas.values():
        ok = e["lat"] is not None and CAIXA_CWB[0] < e["lat"] < CAIXA_CWB[1] and CAIXA_CWB[2] < e["lon"] < CAIXA_CWB[3]
        if not ok:
            fora += 1
            continue
        if e["lula_2t"] + e["flavio_2t"] and e["lula_1t"] + e["flavio_1t"]:
            lista.append(e)
    bairros = [{k: num(v) for k, v in b.items()} for b in ler("curitiba_bairros.csv")]
    contorno = json.loads((PASTA / "curitiba-contorno.geojson").read_text(encoding="utf-8"))
    return {"escolas": lista, "fora_do_mapa": fora, "bairros": bairros, "contorno": contorno}


def ilhas():
    campos = ("municipio", "uf", "lat", "lon", "eleitorado", "lula", "flavio", "pct_lula", "pct_lula_vizinhas",
              "fora_pts", "fora_votos", "pct_lula_1t", "fora_pts_1t")
    return [[num(r[k]) for k in campos] for r in ler("ilhas.csv")]


def abstencao_uf():
    soma = {}
    for r in ler("abstencao_municipios.csv"):
        if r["uf"] == "ZZ" or not r["pct_abstencao_1t"] or not r["pct_abstencao"]:
            continue
        s = soma.setdefault(r["uf"], {"uf": r["uf"], "a2": 0, "base2": 0, "a1": 0, "base1": 0.0})
        a1, p1 = int(r["abstencao_1t"]), float(r["pct_abstencao_1t"])
        s["a2"] += int(r["abstencao"])
        s["base2"] += int(r["abstencao"]) + int(r["comparecimento"])
        s["a1"] += a1
        s["base1"] += a1 / p1 * 100 if p1 else 0
    return [{"uf": s["uf"], "pct_1t": round(s["a1"] / s["base1"] * 100, 2), "pct_2t": round(s["a2"] / s["base2"] * 100, 2),
             "abst_1t": s["a1"], "abst_2t": s["a2"]} for s in soma.values()]


def main():
    dados = {
        "gerado": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "curitiba": curitiba(),
        "ilhas": ilhas(),
        "topo": json.loads((PASTA / "br-estados.topo.json").read_text(encoding="utf-8")),
        "retroativo": [{k: num(v) for k, v in r.items()} for r in ler("retroativo.csv")],
        "transferencia": [{k: num(v) for k, v in r.items()} for r in ler("transferencia.csv")],
        "abstencao": abstencao_uf(),
        "extremos": [{k: num(v) for k, v in r.items()} for r in ler("extremos.csv")],
    }
    html = TEMPLATE.read_text(encoding="utf-8").replace("/*DADOS*/null", json.dumps(dados, ensure_ascii=False, separators=(",", ":")))
    SAIDA.write_text(html, encoding="utf-8")
    c = dados["curitiba"]
    print(f"painel/depois.html: {len(c['escolas'])} escolas de Curitiba no mapa ({c['fora_do_mapa']} com coordenada errada,"
          f" fora do mapa) · {len(dados['ilhas'])} cidades · {len(html) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
