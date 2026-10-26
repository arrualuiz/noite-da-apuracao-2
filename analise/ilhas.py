#!/usr/bin/env python3
"""Ilhas: cidades que votaram muito diferente das vizinhas (uma cidade vermelha no meio de um mar azul).

Para cada cidade, compara o % do Lula (entre Lula e Flávio) com o das 10 cidades mais próximas,
ponderado pelo eleitorado delas. A diferença é o quanto a cidade foge da vizinhança, em pontos.
É a ideia do "Moran local" (LISA): um valor alto cercado de valores baixos, ou o contrário.

Localização de cada cidade: o centroide do município na malha oficial do IBGE. Reserva: a mediana das coordenadas dos locais de votação (dados abertos do TSE,
eleitorado_local_votacao_2026, em dados/municipios_coordenadas.csv), que tem erros de cadastro
(a escola do centro de Luislândia-MG aparece no Sul de Minas). Gera dados/ilhas.csv com todas as cidades.

Também mostra se a cidade já era ilha no 1º turno: se era, é algo do lugar (estrutura), não da campanha.

Uso: python3 analise/abstencao.py && python3 analise/ilhas.py
"""
import csv
import io
import json
import math
import urllib.request
import zipfile
from pathlib import Path

from extremos import ler

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "dados"
PASTA_1T = PASTA / "historico" / "tse" / "1t-municipios"
LOCAIS = PASTA / "historico" / "tse" / "locais" / "eleitorado_local_votacao_2026.zip"
COORD = PASTA / "municipios_coordenadas.csv"
CENTROIDES = PASTA / "historico" / "ibge" / "centroides-municipios.json"
URL_CENTROIDES = "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR/metadados?intrarregiao=municipio"
VIZINHOS = 10


def mil(n):
    return f"{n:,.0f}".replace(",", ".")


def mediana(pontos, i):
    """Mediana ponderada pelos eleitores. Alguns locais têm coordenada errada no cadastro (a escola do
    centro de Luislândia-MG aparece no Sul de Minas), e a média seria puxada por eles; a mediana não."""
    pontos = sorted(pontos, key=lambda p: p[i])
    meio, acum = sum(p[2] for p in pontos) / 2, 0
    for p in pontos:
        acum += p[2]
        if acum >= meio:
            return p[i]


def coordenadas():
    """Centroide de cada município, da malha oficial do IBGE (uma chamada para o Brasil todo). Se faltar,
    a mediana dos locais de votação. Avisa quantas cidades têm locais longe do centroide no cadastro do TSE."""
    locais = coordenadas_locais()
    if not CENTROIDES.exists():
        CENTROIDES.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(URL_CENTROIDES, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            CENTROIDES.write_bytes(r.read())
    ibge = {m["id"]: (m["centroide"]["latitude"], m["centroide"]["longitude"])
            for m in json.loads(CENTROIDES.read_text(encoding="utf-8"))}
    cfg = json.loads((PASTA / "municipios-6258.json").read_text(encoding="utf-8"))
    out, longe = {}, []
    for a in cfg["abr"]:
        for m in a["mu"]:
            c, l = ibge.get(m.get("cdi", "")), locais.get(m["cd"])
            if c and l and km(c, l) > 50:
                longe.append((km(c, l), f"{m['nm'].title()} ({a['cd'].upper()})"))
            if c or l:
                out[m["cd"]] = c or l
    longe.sort(reverse=True)
    print(f"Coordenadas: centroide do IBGE. Em {len(longe)} cidades, a mediana dos locais de votação no cadastro do TSE"
          f" fica a mais de 50 km dele (ex.: {', '.join(f'{n} {d:.0f} km' for d, n in longe[:3])}).\n"
          "Nas cidades enormes da Amazônia isso é normal (o centroide fica na floresta); nas pequenas, é erro de cadastro.\n")
    return out


def coordenadas_locais():
    if COORD.exists():
        return {r["cd_tse"]: (float(r["lat"]), float(r["lon"])) for r in csv.DictReader(COORD.open(encoding="utf-8"))}
    soma = {}
    with zipfile.ZipFile(LOCAIS) as z:
        for nome in z.namelist():
            if not nome.endswith(".csv") or nome.endswith(("_BRASIL.csv", "_ZZ.csv")):
                continue
            with z.open(nome) as fh:
                for r in csv.DictReader(io.TextIOWrapper(fh, encoding="latin-1"), delimiter=";"):
                    if r["NR_TURNO"] != "2":
                        continue
                    try:
                        lat, lon = float(r["NR_LATITUDE"].replace(",", ".")), float(r["NR_LONGITUDE"].replace(",", "."))
                    except ValueError:
                        continue
                    if lat == -1 or lon == -1 or not (-35 < lat < 6 and -75 < lon < -30):
                        continue
                    n = int(r["QT_ELEITOR_SECAO"] or 0) or 1
                    soma.setdefault(r["CD_MUNICIPIO"].zfill(5), []).append((lat, lon, n))
    with COORD.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["cd_tse", "lat", "lon"])
        for cd, pontos in sorted(soma.items()):
            w.writerow([cd, round(mediana(pontos, 0), 5), round(mediana(pontos, 1), 5)])
    return coordenadas_locais()


def km(a, b):
    """Distância aproximada (equiretangular) entre dois pontos (lat, lon)."""
    x = math.radians(b[1] - a[1]) * math.cos(math.radians((a[0] + b[0]) / 2))
    y = math.radians(b[0] - a[0])
    return 6371 * math.hypot(x, y)


def main():
    coord = coordenadas()
    pasta_2t = max((d / "todos-mun" for d in (PASTA / "brutos").iterdir() if (d / "todos-mun").exists()),
                   key=lambda p: p.parent.name)
    cfg = json.loads((PASTA / "municipios-6258.json").read_text(encoding="utf-8"))
    cid = []
    for a in cfg["abr"]:
        if a["cd"] == "zz":
            continue
        for m in a["mu"]:
            f2, f1 = pasta_2t / f"{a['cd']}{m['cd']}.json", PASTA_1T / f"{a['cd']}{m['cd']}.json"
            if m["cd"] not in coord or not (f2.exists() and f1.exists()):
                continue
            x, y = ler(f2, True), ler(f1, False)
            if not (x["lula"] + x["flavio"]) or not (y["lula"] + y["flavio"]):
                continue
            cid.append({"cd": m["cd"], "nome": f"{m['nm'].title()} ({a['cd'].upper()})", "uf": a["cd"].upper(),
                        "pos": coord[m["cd"]], "te": x["te"], "lula": x["lula"], "flavio": x["flavio"],
                        "abst": x["a"] / (x["a"] + x["c"]) * 100,
                        "pl": x["lula"] / (x["lula"] + x["flavio"]) * 100,
                        "pl1": y["lula"] / (y["lula"] + y["flavio"]) * 100,
                        "outros1": (y["vv"] - y["lula"] - y["flavio"]) / y["vv"] * 100})

    # vizinhos: as 10 mais próximas (pré-filtro por uma caixa de ~3 graus para não medir tudo com tudo)
    for c in cid:
        perto = [o for o in cid if o is not c and abs(o["pos"][0] - c["pos"][0]) < 3 and abs(o["pos"][1] - c["pos"][1]) < 3]
        if len(perto) < VIZINHOS:
            perto = [o for o in cid if o is not c]
        viz = sorted(perto, key=lambda o: km(c["pos"], o["pos"]))[:VIZINHOS]
        peso = sum(o["lula"] + o["flavio"] for o in viz)
        c["viz_pl"] = sum(o["pl"] * (o["lula"] + o["flavio"]) for o in viz) / peso
        c["viz_pl1"] = sum(o["pl1"] * (o["lula"] + o["flavio"]) for o in viz) / peso
        c["viz_km"] = km(c["pos"], viz[-1]["pos"])
        c["viz_nomes"] = [o["nome"].rsplit(" (", 1)[0] for o in viz[:3]]
        c["viz_cds"] = [o["cd"] for o in viz]
        c["fora"] = c["pl"] - c["viz_pl"]
        c["fora1"] = c["pl1"] - c["viz_pl1"]
        # votos do Lula além (ou aquém) do que a vizinhança faria com o mesmo número de votos
        c["fora_votos"] = (c["pl"] - c["viz_pl"]) / 100 * (c["lula"] + c["flavio"])

    with (PASTA / "ilhas.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["cd_tse", "municipio", "uf", "lat", "lon", "eleitorado", "lula", "flavio", "pct_lula", "pct_lula_vizinhas",
                     "fora_pts", "fora_votos", "pct_lula_1t", "pct_lula_vizinhas_1t", "fora_pts_1t", "raio_km", "vizinhas"])
        for c in sorted(cid, key=lambda c: -abs(c["fora"])):
            w.writerow([c["cd"], c["nome"].rsplit(" (", 1)[0], c["uf"], *c["pos"], c["te"], c["lula"], c["flavio"],
                        round(c["pl"], 2), round(c["viz_pl"], 2), round(c["fora"], 2), round(c["fora_votos"]),
                        round(c["pl1"], 2), round(c["viz_pl1"], 2), round(c["fora1"], 2), round(c["viz_km"], 1),
                        " ".join(c["viz_cds"])])

    def mostrar(titulo, lista):
        print(titulo)
        for c in lista:
            ja = "já era no 1º turno" if c["fora1"] * c["fora"] > 0 and abs(c["fora1"]) >= abs(c["fora"]) / 2 else "NOVO no 2º turno"
            print(f"  {c['nome']:32} Lula {c['pl']:5.1f}%  vizinhas {c['viz_pl']:5.1f}%  → {c['fora']:+5.1f} pts"
                  f" ({'+' if c['fora_votos'] > 0 else ''}{mil(c['fora_votos'])} votos)  {mil(c['te'])} eleitores · {ja}")
            print(f"  {'':32} 1º turno: {c['pl1']:5.1f}% x vizinhas {c['viz_pl1']:5.1f}% ({c['fora1']:+.1f})"
                  f" · perto de {', '.join(c['viz_nomes'])} · raio {c['viz_km']:.0f} km")
        print()

    print(f"ILHAS · {len(cid)} cidades, cada uma comparada com as {VIZINHOS} mais próximas (% do Lula entre Lula e Flávio)\n")
    vermelhas = [c for c in cid if c["pl"] > 50 and c["viz_pl"] < 50]
    azuis = [c for c in cid if c["pl"] < 50 and c["viz_pl"] > 50]
    print(f"Cidades com o Lula na frente cercadas de vizinhas com o Flávio na frente: {len(vermelhas)}")
    print(f"Cidades com o Flávio na frente cercadas de vizinhas com o Lula na frente: {len(azuis)}\n")
    mostrar("ILHAS VERMELHAS NUM MAR AZUL (o Lula ganhou, as vizinhas deram Flávio), as que mais fogem:",
            sorted(vermelhas, key=lambda c: -c["fora"])[:12])
    mostrar("ILHAS AZUIS NUM MAR VERMELHO (o Flávio ganhou, as vizinhas deram Lula), as que mais fogem:",
            sorted(azuis, key=lambda c: c["fora"])[:12])
    grandes = [c for c in cid if c["te"] >= 50_000]
    mostrar("CIDADES DE 50 MIL ELEITORES OU MAIS QUE MAIS FOGEM DAS VIZINHAS PARA O LADO DO LULA:",
            sorted(grandes, key=lambda c: -c["fora"])[:8])
    mostrar("CIDADES DE 50 MIL ELEITORES OU MAIS QUE MAIS FOGEM DAS VIZINHAS PARA O LADO DO FLÁVIO:",
            sorted(grandes, key=lambda c: c["fora"])[:8])
    mostrar("O QUE MAIS MUDOU DE UM TURNO PARA O OUTRO EM RELAÇÃO ÀS VIZINHAS (virou ilha no 2º turno):",
            sorted(cid, key=lambda c: -abs(c["fora"] - c["fora1"]))[:8])
    print("Gravado em dados/ilhas.csv")


if __name__ == "__main__":
    main()
