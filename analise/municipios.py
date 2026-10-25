#!/usr/bin/env python3
"""Voto por município x soja (case 21): o resultado oficial do TSE por município, cruzado com o IBGE.

Uso: python3 analise/municipios.py

Baixa (com cache em dados/historico/tse/ e dados/historico/ibge/, fora do git):
  - votacao_partido_munzona_<ano>.zip (TSE, dados abertos): votos de Presidente por município e zona, 2022 e 2026
  - mun-e006257-cm.json (TSE): lista de municípios, com o código do IBGE de cada um
  - IBGE/SIDRA: área plantada de soja em 2025 (PAM, tabela 5457), área territorial (Censo 2022, tabela 4714)
    e moradores por região de nascimento (Censo 2022, tabela 631)
Gera:
  dados/export/municipios.csv   uma linha por município: votos de PL e PT no 1º turno de 2026 e de 2022,
                                área, soja e moradores nascidos no Sul
E imprime as tabelas do case 21. As funções de cálculo também são usadas por analise/graficos.py.
"""
import csv
import gzip
import io
import json
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TSE = RAIZ / "dados" / "historico" / "tse"
IBGE = RAIZ / "dados" / "historico" / "ibge"
SAIDA = RAIZ / "dados" / "export" / "municipios.csv"
CDN = "https://cdn.tse.jus.br/estatistica/sead/odsele"
CM = "https://resultados.tse.jus.br/oficial/ele2026/6257/config/mun-e006257-cm.json"
SIDRA = {
    "soja-2025": "https://apisidra.ibge.gov.br/values/t/5457/n6/all/v/8331/p/2025/c782/40124",
    "area-2022": "https://apisidra.ibge.gov.br/values/t/4714/n6/all/v/6318/p/2022",
    "nascimento-2022": "https://apisidra.ibge.gov.br/values/t/631/n6/all/v/93/p/2022/c2/0/c183/0,95314",
}
REGIAO = {"1": "Norte", "2": "Nordeste", "3": "Sudeste", "4": "Sul", "5": "Centro-Oeste"}
FAIXAS = ["sem soja", "até 1%", "1–5%", "5–15%", "15–30%", "mais de 30%"]
COLUNAS = ["ibge", "tse", "uf", "regiao", "municipio", "validos_2026", "flavio_2026", "lula_2026", "margem_2026_pp",
           "validos_2022", "bolsonaro_2022", "lula_2022", "margem_2022_pp", "area_km2", "soja_ha_2025",
           "pct_soja_territorio", "populacao_2022", "nascidos_sul_2022", "pct_nascidos_sul"]


def baixar(url, arq):
    if not arq.exists():
        arq.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=300) as r:
            dados = r.read()
            arq.write_bytes(gzip.decompress(dados) if r.headers.get("Content-Encoding") == "gzip" else dados)
    return arq


def num(v):
    """Valor do SIDRA: '-' é zero; '...' e 'X' (sem dado ou sigiloso) também viram zero."""
    try:
        return float(v)
    except ValueError:
        return 0.0


def votos(ano):
    """1º turno de Presidente por município (código TSE): válidos, PL (22) e PT (13). Sem o exterior."""
    z = zipfile.ZipFile(baixar(f"{CDN}/votacao_partido_munzona/votacao_partido_munzona_{ano}.zip",
                               TSE / f"votacao_partido_munzona_{ano}.zip"))
    nome = next(n for n in z.namelist() if n.endswith("_BR.csv"))
    mun = defaultdict(lambda: defaultdict(int))
    with z.open(nome) as fh:
        for r in csv.DictReader(io.TextIOWrapper(fh, encoding="latin-1"), delimiter=";"):
            if r["CD_CARGO"] != "1" or r["NR_TURNO"] != "1" or r["SG_UF"] == "ZZ":
                continue
            v = int(r.get("QT_VOTOS_NOMINAIS_VALIDOS") or r.get("QT_VOTOS_NOMINAIS") or 0)
            m = mun[r["CD_MUNICIPIO"].zfill(5)]
            m["validos"] += v
            m[r["NR_PARTIDO"]] += v
    return mun


def sidra(nome):
    return json.loads(baixar(SIDRA[nome], IBGE / f"{nome}.json").read_text(encoding="utf-8"))[1:]


def malha(cod):
    """Área e nome de um município criado depois do Censo 2022 (API de malhas do IBGE)."""
    url = f"https://servicodados.ibge.gov.br/api/v4/malhas/municipios/{cod}/metadados"
    d = json.loads(baixar(url, IBGE / f"malha-{cod}.json").read_text(encoding="utf-8"))[0]
    return float(d["area"]["dimensao"]), d["nome"]


def montar():
    cm = json.loads(baixar(CM, TSE / "mun-e006257-cm.json").read_text(encoding="utf-8"))
    munis = [(a["cd"].upper(), m) for a in cm["abr"] if a["cd"] != "zz" for m in a["mu"]]
    v26, v22 = votos(2026), votos(2022)
    soja = {r["D1C"]: num(r["V"]) for r in sidra("soja-2025")}
    area = {r["D1C"]: num(r["V"]) for r in sidra("area-2022")}
    nome = {r["D1C"]: r["D1N"].rsplit(" - ", 1)[0] for r in sidra("area-2022")}
    nasc = defaultdict(dict)
    for r in sidra("nascimento-2022"):
        nasc[r["D1C"]][r["D5C"]] = num(r["V"])   # D5C: 0 = total, 95314 = nascidos na Região Sul
    linhas = []
    for uf, m in munis:
        cod, a, b = m["cdi"], v26[m["cd"]], v22.get(m["cd"])
        ar, nm = (area[cod], nome[cod]) if cod in area else malha(cod)
        pop, sul = nasc[cod].get("0"), nasc[cod].get("95314")
        linhas.append([cod, m["cd"], uf, REGIAO[cod[0]], nm,
                       a["validos"], a["22"], a["13"], round((a["22"] - a["13"]) / a["validos"] * 100, 2),
                       b["validos"] if b else "", b["22"] if b else "", b["13"] if b else "",
                       round((b["22"] - b["13"]) / b["validos"] * 100, 2) if b else "",
                       ar, soja.get(cod, 0.0), round(soja.get(cod, 0.0) / (ar * 100) * 100, 2),
                       int(pop) if pop else "", int(sul) if pop else "", round(sul / pop * 100, 2) if pop else ""])
    return linhas


# ---------------------------------------------------------------- cálculos (também usados por graficos.py)
def ler():
    with SAIDA.open(encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        for k in COLUNAS[5:]:
            r[k] = float(r[k]) if r[k] != "" else None
    return rows


def faixa(pct):
    if pct == 0:
        return "sem soja"
    return "até 1%" if pct <= 1 else "1–5%" if pct <= 5 else "5–15%" if pct <= 15 else "15–30%" if pct <= 30 else "mais de 30%"


def porte(validos):
    return "<10 mil" if validos < 1e4 else "10–50 mil" if validos < 5e4 else "50–200 mil" if validos < 2e5 else "200 mil+"


def colunas(ano):
    return (f"validos_{ano}", f"flavio_{ano}" if ano == 2026 else f"bolsonaro_{ano}", f"lula_{ano}")


def margem(rows, ano=2026):
    """Margem PL − PT (p.p. dos válidos) de um conjunto de municípios, ponderada pelos votos."""
    v, p, t = colunas(ano)
    rows = [r for r in rows if r[v]]
    tot = sum(r[v] for r in rows)
    return (sum(r[p] for r in rows) - sum(r[t] for r in rows)) / tot * 100 if tot else None


def vs_vizinhos(rows, ano=2026, classe=faixa):
    """Margem de cada classe de soja menos a dos municípios SEM soja do mesmo estado e do mesmo porte.

    Devolve {classe: (diferença em p.p., municípios comparados, municípios na classe)}. O grupo de comparação de
    cada município é o conjunto dos municípios sem soja da mesma UF e do mesmo porte (votos válidos de 2026).
    `classe` diz em que grupo cai cada % de soja (None = fica de fora da comparação).
    """
    v, p, t = colunas(ano)
    rows = [r for r in rows if r[v]]
    grupo = defaultdict(lambda: [0.0, 0.0])
    for r in rows:
        if r["pct_soja_territorio"] == 0:
            g = grupo[(r["uf"], porte(r["validos_2026"]))]
            g[0] += r[v]; g[1] += r[p] - r[t]
    base = lambda r: grupo[(r["uf"], porte(r["validos_2026"]))]
    out = {}
    for c in dict.fromkeys(classe(r["pct_soja_territorio"]) for r in rows):
        if c in (None, "sem soja"):
            continue
        sel = [r for r in rows if classe(r["pct_soja_territorio"]) == c]
        ok = [r for r in sel if base(r)[0] > 0]
        tot = sum(r[v] for r in ok)
        dif = sum(r[v] * ((r[p] - r[t]) / r[v] * 100 - base(r)[1] / base(r)[0] * 100) for r in ok) / tot if tot else None
        out[c] = (dif, len(ok), len(sel))
    return out


# ---------------------------------------------------------------- relatório
def br(v, d=1, sinal=False):
    s = f"{v:+,.{d}f}" if sinal else f"{v:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def relatorio(rows):
    tv = sum(r["validos_2026"] for r in rows)
    ta = sum(r["area_km2"] for r in rows)
    fl, lu = sum(r["flavio_2026"] for r in rows), sum(r["lula_2026"] for r in rows)
    print(f"\nConferência 2026 (sem o exterior): Flávio {br(fl, 0)} x Lula {br(lu, 0)}, {br(tv, 0)} válidos, "
          f"{len(rows)} municípios")
    soja_maior = [r for r in rows if r["pct_soja_territorio"] > 100]
    for r in soja_maior:
        print(f"  ! {r['municipio']} ({r['uf']}): {br(r['soja_ha_2025'], 0)} ha de soja em "
              f"{br(r['area_km2'] * 100, 0)} ha de área (dado do IBGE maior que o território)")

    print("\n1. Por faixa de soja (área plantada em 2025 ÷ área do município)")
    print("| Soja no território | Municípios | % da área | % dos votos | Flávio | Lula | Margem PL − PT 2026 | Saldo PL − PT 2026 | Margem 2022 |")
    print("|---|---|---|---|---|---|---|---|---|")
    for f in FAIXAS:
        sel = [r for r in rows if faixa(r["pct_soja_territorio"]) == f]
        v = sum(r["validos_2026"] for r in sel)
        a, b = sum(r["flavio_2026"] for r in sel), sum(r["lula_2026"] for r in sel)
        print(f"| {f} | {len(sel)} | {br(sum(r['area_km2'] for r in sel) / ta * 100)}% | {br(v / tv * 100)}% | "
              f"{br(a / v * 100)}% | {br(b / v * 100)}% | {br(margem(sel), 1, True)} | {br((a - b) / 1e6, 2, True)} mi | "
              f"{br(margem(sel, 2022), 1, True)} |")
    soja15 = [r for r in rows if r["pct_soja_territorio"] > 15]
    s15 = sum(r["flavio_2026"] - r["lula_2026"] for r in soja15)
    print(f"Soja > 15% do território: {len(soja15)} municípios, {br(sum(r['validos_2026'] for r in soja15) / tv * 100)}% "
          f"dos votos, saldo PL − PT {br(s15 / 1e6, 2, True)} mi; nos demais, {br((fl - lu - s15) / 1e6, 2, True)} mi")

    print("\n2. Comparando com os municípios sem soja do mesmo estado e do mesmo porte (p.p.)")
    c26, c22 = vs_vizinhos(rows, 2026), vs_vizinhos(rows, 2022)
    print("| Soja no território | Margem no país (2026) | Diferença para os vizinhos sem soja (2026) | (2022) | Municípios comparados |")
    print("|---|---|---|---|---|")
    for f in FAIXAS[1:]:
        sel = [r for r in rows if faixa(r["pct_soja_territorio"]) == f]
        print(f"| {f} | {br(margem(sel), 1, True)} | {br(c26[f][0], 1, True)} | {br(c22[f][0], 1, True)} | "
              f"{c26[f][1]} de {c26[f][2]} |")

    print("\n3. Por região: municípios com soja em 5% ou mais do território x sem soja do mesmo estado e porte")
    print("| Região | Municípios | Margem dos sem soja | Margem dos com soja ≥ 5% | Diferença (mesmo estado e porte) |")
    print("|---|---|---|---|---|")
    for reg in ["Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste"]:
        rr = [r for r in rows if r["regiao"] == reg]
        com = [r for r in rr if r["pct_soja_territorio"] >= 5]
        cinco = lambda p: "sem soja" if p == 0 else "≥ 5%" if p >= 5 else None
        d = vs_vizinhos(rr, classe=cinco).get("≥ 5%")
        sem = [r for r in rr if r["pct_soja_territorio"] == 0]
        print(f"| {reg} | {len(com)} | {br(margem(sem), 1, True)} | {br(margem(com), 1, True)} | "
              f"{br(d[0], 1, True) if d else '—'} |")

    ne = [r for r in rows if r["regiao"] == "Nordeste"]
    print("\n4. Nordeste: os 10 municípios com mais área de soja")
    print("| Município | Soja (mil ha) | % do território | Flávio | Lula | Margem PL − PT | 2022 |")
    print("|---|---|---|---|---|---|---|")
    for r in sorted(ne, key=lambda r: -r["soja_ha_2025"])[:10]:
        v = r["validos_2026"]
        print(f"| {r['municipio']} ({r['uf']}) | {br(r['soja_ha_2025'] / 1e3, 0)} | {br(r['pct_soja_territorio'])}% | "
              f"{br(r['flavio_2026'] / v * 100)}% | {br(r['lula_2026'] / v * 100)}% | {br(r['margem_2026_pp'], 1, True)} | "
              f"{br(r['margem_2022_pp'], 1, True)} |")
    for lim in (5, 15):
        sel = [r for r in ne if r["pct_soja_territorio"] >= lim]
        venc = [r["municipio"] for r in sel if r["flavio_2026"] > r["lula_2026"]]
        print(f"Nordeste, soja ≥ {lim}% do território: {len(sel)} municípios; o Flávio venceu em {len(venc)} "
              f"({', '.join(venc)})")

    print("\n5. Oeste da Bahia e vizinhos do Tocantins")
    print("| Município | Válidos | Flávio | Lula | Soja (% do território) | Nascidos no Sul |")
    print("|---|---|---|---|---|---|")
    oeste = {("BA", n) for n in ["Luís Eduardo Magalhães", "Barreiras", "São Desidério", "Formosa do Rio Preto",
                                 "Correntina", "Riachão das Neves", "Jaborandi"]}
    oeste |= {("TO", n) for n in ["Taguatinga", "Ponte Alta do Bom Jesus", "Aurora do Tocantins", "Dianópolis",
                                  "Novo Jardim", "Taipas do Tocantins", "Mateiros"]}
    for r in sorted([r for r in rows if (r["uf"], r["municipio"]) in oeste], key=lambda r: (r["uf"], -r["pct_soja_territorio"])):
        v = r["validos_2026"]
        print(f"| {r['municipio']} ({r['uf']}) | {br(v, 0)} | {br(r['flavio_2026'] / v * 100)}% | "
              f"{br(r['lula_2026'] / v * 100)}% | {br(r['pct_soja_territorio'])}% | {br(r['pct_nascidos_sul'])}% |")
    for uf in ("BA", "TO"):
        print(f"{uf}: margem PL − PT {br(margem([r for r in rows if r['uf'] == uf]), 1, True)}")

    print("\n6. Norte e Nordeste: soja x moradores nascidos no Sul (Censo 2022)")
    print("| Região | Grupo | Municípios | Votos válidos | Margem PL − PT |")
    print("|---|---|---|---|---|")
    grupos = [("soja ≥ 5%, nascidos no Sul ≥ 5%", lambda r: r["pct_soja_territorio"] >= 5 and r["pct_nascidos_sul"] >= 5),
              ("soja ≥ 5%, nascidos no Sul < 5%", lambda r: r["pct_soja_territorio"] >= 5 and r["pct_nascidos_sul"] < 5),
              ("soja < 5%, nascidos no Sul ≥ 5%", lambda r: r["pct_soja_territorio"] < 5 and r["pct_nascidos_sul"] >= 5),
              ("soja < 5%, nascidos no Sul < 5%", lambda r: r["pct_soja_territorio"] < 5 and r["pct_nascidos_sul"] < 5)]
    for reg in ["Norte", "Nordeste"]:
        rr = [r for r in rows if r["regiao"] == reg and r["pct_nascidos_sul"] is not None]
        for rot, cond in grupos:
            sel = [r for r in rr if cond(r)]
            if sel:
                print(f"| {reg} | {rot} | {len(sel)} | {br(sum(r['validos_2026'] for r in sel) / 1e3, 0)} mil | "
                      f"{br(margem(sel), 1, True)} |")


def main():
    linhas = montar()
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(COLUNAS)
        w.writerows(sorted(linhas))
    print(f"municípios: {len(linhas)} linhas → dados/export/municipios.csv")
    relatorio(ler())


if __name__ == "__main__":
    main()
