#!/usr/bin/env python3
"""As páginas com o resultado final, em gráficos: painel/depois.html (o Brasil), painel/curitiba.html e
painel/crescimento.html (do 1º para o 2º turno, em todas as eleições desde 2002).

Junta os CSVs gerados pelos outros scripts e grava cada página a partir do seu template
(painel/depois-template.html e painel/curitiba-template.html), trocando /*DADOS*/null pelo JSON.
O estilo e as funções comuns ficam em painel/comum.css e painel/comum.js. Para mudar uma página:
editar o template (ou o comum.*), rodar este script e fazer o commit e o push; o GitHub Pages atualiza.
  - Curitiba por escola e por bairro      dados/curitiba_secoes.csv, dados/curitiba_bairros.csv (analise/bairros.py)
                                         e o contorno do município, dados/curitiba-contorno.geojson (IBGE, malha
                                         municipal: servicodados.ibge.gov.br/api/v3/malhas/municipios/4106902)
                                         e os 75 bairros, dados/curitiba-bairros.topo.json (malha do IPPUC, pelo
                                         repositório github.com/gustavokira/geo-curitiba)
  - Curitiba e as capitais desde 2002     dados/historico/capitais_presidente.csv (analise/capitais_historia.py)
  - Curitiba por bairro, 2002 a 2026, e o Censo 2022 por bairro: dados/curitiba_bairros_historia.csv e
                                         dados/curitiba_bairros_censo.csv (analise/curitiba_historia.py)
  - do 1º para o 2º turno, 2002 a 2026     dados/crescimento.csv (analise/crescimento.py): crescimento.html e Curitiba
  - ilhas: cidades x vizinhas            dados/ilhas.csv (analise/ilhas.py)
  - a previsão olhando para trás         dados/retroativo.csv (analise/retroativo.py)
  - para onde foram os votos do 1º turno dados/transferencia.csv (analise/transferencia.py)
  - abstenção por estado                 dados/abstencao_municipios.csv (analise/abstencao.py)
  - mínimos e máximos                    dados/extremos.csv (analise/extremos.py)

Uso: python3 analise/depois.py
"""
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from bairros import nome_proprio

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "dados"
PAINEL = RAIZ / "painel"
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
    malha = json.loads((PASTA / "curitiba-bairros.topo.json").read_text(encoding="utf-8"))
    for g in malha["objects"]["bairros"]["geometries"]:
        g["properties"] = {"nome": nome_proprio(g["properties"]["nome"])}
    hist = [{k: v if k == "bairro" else num(v) for k, v in r.items()} for r in ler("curitiba_bairros_historia.csv")]
    censo = [{k: v if k == "bairro" else num(v) for k, v in r.items()} for r in ler("curitiba_bairros_censo.csv")]
    return {"escolas": lista, "fora_do_mapa": fora, "bairros": bairros, "contorno": contorno, "malha": malha,
            "hist": hist, "censo": censo}


def historia():
    """PT no 1º turno (% dos válidos) e no 2º (% entre os dois) em cada capital, no Paraná e no Brasil."""
    v = {}
    for r in ler("historico/capitais_presidente.csv"):
        k = (int(r["ano"]), int(r["turno"]), r["cd_tse"])
        x = v.setdefault(k, {"municipio": r["municipio"], "uf": r["uf"], "votos": defaultdict(int)})
        x["votos"][r["partido"]] += int(r["votos"])
    out = {}
    for (ano, turno, cd), x in v.items():
        vt = x["votos"]
        pt = vt.get("PT", 0)
        if turno == 1:
            pct = pt / sum(vt.values()) * 100
        else:
            pct = pt / (pt + max(n for p, n in vt.items() if p != "PT")) * 100
        o = out.setdefault(cd, {"cd": cd, "municipio": x["municipio"], "uf": x["uf"], "t1": {}, "t2": {}})
        o[f"t{turno}"][ano] = round(pct, 2)
    return list(out.values())


def ilhas():
    """Cada cidade x as vizinhas, com o código do IBGE (para achar o desenho do município na malha
    painel/br-municipios.topo.json) e os códigos das 10 vizinhas usadas na conta."""
    cfg = json.loads((PASTA / "municipios-6258.json").read_text(encoding="utf-8"))
    ibge = {m["cd"]: m.get("cdi", "") for a in cfg["abr"] for m in a["mu"]}
    campos = ("municipio", "uf", "lat", "lon", "eleitorado", "lula", "flavio", "pct_lula", "pct_lula_vizinhas",
              "fora_pts", "fora_votos", "pct_lula_1t", "fora_pts_1t")
    return [[ibge.get(r["cd_tse"], "")] + [num(r[k]) for k in campos] + [" ".join(ibge.get(v, "") for v in r["vizinhas"].split())]
            for r in ler("ilhas.csv")]


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


def gravar(nome, dados):
    html = (PAINEL / f"{nome}-template.html").read_text(encoding="utf-8").replace(
        "/*DADOS*/null", json.dumps(dados, ensure_ascii=False, separators=(",", ":")))
    (PAINEL / f"{nome}.html").write_text(html, encoding="utf-8")
    return len(html)


def main():
    gerado = datetime.now().strftime("%d/%m/%Y %H:%M")
    c = curitiba()
    cresc = [{k: v if k == "lugar" else num(v) for k, v in r.items()} for r in ler("crescimento.csv")]
    n = gravar("curitiba", {"gerado": gerado, "curitiba": c, "historia": historia(),
                            "eleicoes": [r for r in cresc if r["lugar"] in ("75353", "PR", "BR")]})
    print(f"painel/curitiba.html: {len(c['escolas'])} escolas no mapa ({c['fora_do_mapa']} com coordenada errada,"
          f" fora do mapa) · {len(c['bairros'])} bairros com votos · {n / 1e6:.1f} MB")
    dados = {
        "gerado": gerado,
        "ilhas": ilhas(),
        "retroativo": [{k: num(v) for k, v in r.items()} for r in ler("retroativo.csv")],
        "transferencia": [{k: num(v) for k, v in r.items()} for r in ler("transferencia.csv")],
        "abstencao": abstencao_uf(),
        "extremos": [{k: num(v) for k, v in r.items()} for r in ler("extremos.csv")],
    }
    n = gravar("depois", dados)
    print(f"painel/depois.html: {len(dados['ilhas'])} cidades · {n / 1e6:.1f} MB")
    n = gravar("crescimento", {"gerado": gerado, "linhas": cresc})
    print(f"painel/crescimento.html: {len(cresc)} linhas (lugar x eleição) · {n / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
