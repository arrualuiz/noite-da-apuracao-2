#!/usr/bin/env python3
"""Do 1º para o 2º turno, em todas as eleições em que o PT foi ao 2º turno (2002 a 2026), em cada lugar.

Para o Brasil, as 5 regiões, os 27 estados e as 27 capitais: votos do PT e do rival no 1º e no 2º turno,
os votos dos outros candidatos no 1º turno, e quem foi votar (aptos, comparecimento, abstenção, brancos
e nulos) nos dois turnos.

Fontes:
  - votos por estado, 2002 a 2022: dados/historico/presidente_votos_uf.csv (analise/historico_tse.py)
  - votos das capitais, 2002 a 2026: dados/historico/capitais_presidente.csv (analise/capitais_historia.py)
  - comparecimento por estado e capital, 2002 a 2022: detalhe_votacao_munzona_<ano>.zip (dados abertos do TSE,
    no cache deste projeto ou no do noite-do-primeiro-turno-2026)
  - 2026: resultado final do 1º turno (dados/historico/2026-t1-uf.csv e os arquivos de município) e a última
    coleta do 2º turno

Gera dados/crescimento.csv (uma linha por lugar e ano). Uso: python3 analise/crescimento.py
"""
import csv
import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "dados"
CACHES = [PASTA / "historico" / "tse", RAIZ.parent / "xx-noite-do-primeiro-turno-2026" / "dados" / "historico" / "tse"]
ANOS = [2002, 2006, 2010, 2014, 2018, 2022, 2026]
RIVAL = {2002: "PSDB", 2006: "PSDB", 2010: "PSDB", 2014: "PSDB", 2018: "PSL", 2022: "PL", 2026: "PL"}
CANDIDATOS = {2002: ("Lula", "Serra"), 2006: ("Lula", "Alckmin"), 2010: ("Dilma", "Serra"), 2014: ("Dilma", "Aécio"),
              2018: ("Haddad", "Bolsonaro"), 2022: ("Lula", "Bolsonaro"), 2026: ("Lula", "Flávio Bolsonaro")}
REGIOES = {"Norte": "AC AM AP PA RO RR TO", "Nordeste": "AL BA CE MA PB PE PI RN SE",
           "Centro-Oeste": "DF GO MS MT", "Sudeste": "ES MG RJ SP", "Sul": "PR RS SC"}
REGIAO = {uf: r for r, ufs in REGIOES.items() for uf in ufs.split()}
NOMES_UF = {"AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia", "CE": "Ceará",
            "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão", "MG": "Minas Gerais",
            "MS": "Mato Grosso do Sul", "MT": "Mato Grosso", "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco",
            "PI": "Piauí", "PR": "Paraná", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RO": "Rondônia",
            "RR": "Roraima", "RS": "Rio Grande do Sul", "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo",
            "TO": "Tocantins"}


def capitais():
    cfg = json.loads((PASTA / "municipios-6258.json").read_text(encoding="utf-8"))
    return {m["cd"]: (a["cd"].upper(), m["nm"].title()) for a in cfg["abr"] for m in a["mu"] if m.get("c") == "s"}


def chaves(uf, cd, caps):
    """Os lugares em que um voto entra: Brasil, região, estado e (se for capital) a capital."""
    out = ["BR"]
    if uf in REGIAO:
        out += [REGIAO[uf], uf]
    if cd in caps:
        out.append(cd)
    return out


def votos(caps):
    """v[(ano, turno, lugar)][partido] = votos."""
    v = defaultdict(lambda: defaultdict(int))
    for r in csv.DictReader((PASTA / "historico" / "presidente_votos_uf.csv").open(encoding="utf-8")):
        for k in chaves(r["uf"], None, caps):
            v[(int(r["ano"]), int(r["turno"]), k)][r["partido"]] += int(r["votos"])
    for r in csv.DictReader((PASTA / "historico" / "capitais_presidente.csv").open(encoding="utf-8")):
        if r["cd_tse"] in caps:
            v[(int(r["ano"]), int(r["turno"]), r["cd_tse"])][r["partido"]] += int(r["votos"])
    # 2026 por estado: 1º turno final e última coleta do 2º
    for r in csv.DictReader((PASTA / "historico" / "2026-t1-uf.csv").open(encoding="utf-8")):
        for k in chaves(r["uf"], None, caps):
            for p, c in (("PT", "lula"), ("PL", "flavio"), ("OUTROS", "outros")):
                v[(2026, 1, k)][p] += int(r[c])
    ultima = sorted(d for d in (PASTA / "brutos").iterdir() if (d / "br-u.json").exists())[-1]
    for arq in ultima.glob("??-u.json"):
        uf = arq.name[:2].upper()
        if uf == "BR":
            continue
        u = json.loads(arq.read_text(encoding="utf-8"))
        c = {x["n"]: int(x["vap"]) for a in u["carg"][0]["agr"] for p in a["par"] for x in p["cand"]}
        for k in chaves(uf, None, caps):
            v[(2026, 2, k)]["PT"] += c.get("13", 0)
            v[(2026, 2, k)]["PL"] += c.get("22", 0)
    return v


def comparecimento(caps):
    """c[(ano, turno, lugar)] = {aptos, comparecimento, abstencoes, brancos, nulos}."""
    c = defaultdict(lambda: defaultdict(int))
    campos = {"QT_APTOS": "aptos", "QT_COMPARECIMENTO": "comparecimento", "QT_ABSTENCOES": "abstencoes",
              "QT_VOTOS_BRANCOS": "brancos", "QT_TOTAL_VOTOS_NULOS": "nulos"}
    for ano in ANOS[:-1]:
        arq = next((p / f"detalhe_votacao_munzona_{ano}.zip" for p in CACHES if (p / f"detalhe_votacao_munzona_{ano}.zip").exists()), None)
        if arq is None:
            print(f"  ! sem detalhe_votacao_munzona_{ano}.zip (rode analise/historico_tse.py)")
            continue
        z = zipfile.ZipFile(arq)
        nome = next(n for n in z.namelist() if n.endswith("_BRASIL.csv"))
        with z.open(nome) as fh:
            for r in csv.DictReader(io.TextIOWrapper(fh, encoding="latin-1"), delimiter=";"):
                if r["CD_CARGO"] != "1":
                    continue
                for k in chaves(r["SG_UF"], r["CD_MUNICIPIO"].zfill(5), caps):
                    for de, para in campos.items():
                        c[(ano, int(r["NR_TURNO"]), k)][para] += int(r[de] or 0)
    # 2026: arquivos do TSE desta eleição (estado, Brasil e capitais), 1º turno final e última coleta do 2º
    pastas = {1: sorted((RAIZ.parent / "xx-noite-do-primeiro-turno-2026" / "dados" / "brutos").glob("*/br-u.json"))[-1].parent,
              2: sorted((PASTA / "brutos").glob("*/br-u.json"))[-1].parent}
    mun = {1: PASTA / "historico" / "tse" / "1t-municipios",
           2: max((d / "todos-mun" for d in (PASTA / "brutos").iterdir() if (d / "todos-mun").exists()), key=lambda p: p.parent.name)}
    for t in (1, 2):
        arquivos = [(k, pastas[t] / f"{k.lower()}-u.json") for k in ["BR"] + list(REGIAO)]
        arquivos += [(cd, mun[t] / f"{uf.lower()}{cd}.json") for cd, (uf, _) in caps.items()]
        for k, arq in arquivos:
            u = json.loads(arq.read_text(encoding="utf-8"))
            e, vv = u["e"], u["v"]
            x = {"aptos": int(e["te"]), "comparecimento": int(e["c"]), "abstencoes": int(e["a"]),
                 "brancos": int(vv["vb"]), "nulos": int(vv["tvn"])}
            for kk in ([k, REGIAO[k]] if k in REGIAO else [k]):
                for n, val in x.items():
                    c[(2026, t, kk)][n] += val
    return c


def main():
    caps = capitais()
    v, c = votos(caps), comparecimento(caps)
    lugares = [("Brasil", "BR", "Brasil", "", "")] + [("Região", r, r, "", r) for r in REGIOES] + \
              [("Estado", uf, NOMES_UF[uf], uf, REGIAO[uf]) for uf in sorted(REGIAO)] + \
              [("Capital", cd, nm, uf, REGIAO.get(uf, "")) for cd, (uf, nm) in sorted(caps.items(), key=lambda x: x[1][1])]
    linhas = []
    for nivel, k, nome, uf, reg in lugares:
        for ano in ANOS:
            v1, v2 = v.get((ano, 1, k)), v.get((ano, 2, k))
            if not v1 or not v2:
                continue
            rival = RIVAL[ano]
            c1, c2 = c.get((ano, 1, k), {}), c.get((ano, 2, k), {})
            linhas.append({
                "nivel": nivel, "lugar": k, "nome": nome, "uf": uf, "regiao": reg, "ano": ano,
                "pt": CANDIDATOS[ano][0], "rival": CANDIDATOS[ano][1],
                "pt_1t": v1.get("PT", 0), "rival_1t": v1.get(rival, 0),
                "outros_1t": sum(v1.values()) - v1.get("PT", 0) - v1.get(rival, 0),
                "pt_2t": v2.get("PT", 0), "rival_2t": v2.get(rival, 0),
                **{f"{n}_{t}": x.get(n, "") for t, x in (("1t", c1), ("2t", c2))
                   for n in ("aptos", "comparecimento", "abstencoes", "brancos", "nulos")},
            })
    with (PASTA / "crescimento.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)

    mil = lambda n: f"{n:+,.0f}".replace(",", ".")
    print(f"{'':10}{'PT 1º → 2º':>26}{'rival 1º → 2º':>28}{'outros no 1º':>14}{'abstenção':>12}   Curitiba")
    for l in (x for x in linhas if x["lugar"] == "75353"):
        print(f"{l['ano']:<6}{l['pt']:>8} {l['pt_1t']:>9,} → {l['pt_2t']:>9,} ({mil(l['pt_2t'] - l['pt_1t'])})".replace(",", ".") +
              f"  {l['rival']:>9} {mil(l['rival_2t'] - l['rival_1t'])}  {l['outros_1t']:>10,}".replace(",", ".") +
              (f"  {mil(l['abstencoes_2t'] - l['abstencoes_1t'])}" if l["abstencoes_1t"] != "" else ""))
    print(f"\n{len(linhas)} linhas em dados/crescimento.csv ({len(lugares)} lugares x {len(ANOS)} eleições)")


if __name__ == "__main__":
    main()
