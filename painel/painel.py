#!/usr/bin/env python3
"""Gera painel.html a partir dos dados coletados (TSE + evolução do UOL).

Uso: python3 painel/painel.py   (o coletar.py chama isto a cada coleta)
"""
import csv
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "dados"
TEMPLATE = Path(__file__).resolve().parent / "template.html"
SAIDA = Path(__file__).resolve().parent / "painel.html"

NOMES = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão", "MG": "Minas Gerais",
    "MS": "Mato Grosso do Sul", "MT": "Mato Grosso", "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco",
    "PI": "Piauí", "PR": "Paraná", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RO": "Rondônia",
    "RR": "Roraima", "RS": "Rio Grande do Sul", "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo",
    "TO": "Tocantins", "ZZ": "Exterior",
}
REGIOES = {
    "Norte": ["AC", "AM", "AP", "PA", "RO", "RR", "TO"],
    "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Centro-Oeste": ["DF", "GO", "MS", "MT"],
    "Sudeste": ["ES", "MG", "RJ", "SP"],
    "Sul": ["PR", "RS", "SC"],
    "Exterior": ["ZZ"],
}
REGIAO_DE = {uf: r for r, ufs in REGIOES.items() for uf in ufs}


def f(s):
    return float(str(s).replace(",", "."))


def ler_csv(nome):
    arq = PASTA / nome
    if not arq.exists():
        return []
    with arq.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def ler_json(caminho):
    try:
        return json.loads(Path(caminho).read_text(encoding="utf-8"))
    except Exception:
        return None


def resumo_tse(u):
    """Extrai totais e candidatos de um arquivo -u.json do TSE."""
    cands = []
    for agr in u["carg"][0]["agr"]:
        for par in agr["par"]:
            for c in par["cand"]:
                cands.append({"num": c["n"], "nome": c["nmu"].title(), "votos": int(c["vap"]), "pct": f(c["pvapn"])})
    cands.sort(key=lambda c: -c["votos"])
    e, s, v = u["e"], u["s"], u["v"]
    return {
        "secoes_pct": f(s["pstn"]),
        "eleitorado": int(e["te"]),
        "eleitorado_apurado": int(e["est"]),
        "comparecimento": int(e["c"]),
        "abstencao": int(e["a"]),
        "total": int(v["tv"]),
        "validos": int(v["vv"]),
        "brancos": int(v["vb"]),
        "nulos": int(v["tvn"]),
        "secoes": int(s["st"]),
        "secoes_total": int(s["ts"]),
        "cands": cands,
    }


def somar(resumos):
    """Nacional como soma das UFs + exterior (o arquivo nacional do TSE atrasa em relação aos estados)."""
    tot = {k: sum(r[k] for r in resumos) for k in
           ("eleitorado", "eleitorado_apurado", "comparecimento", "abstencao", "total", "validos", "brancos", "nulos", "secoes", "secoes_total")}
    votos, nomes = {}, {}
    for r in resumos:
        for c in r["cands"]:
            votos[c["num"]] = votos.get(c["num"], 0) + c["votos"]
            nomes[c["num"]] = c["nome"]
    tot["cands"] = sorted(({"num": n, "nome": nomes[n], "votos": v, "pct": v / tot["validos"] * 100}
                           for n, v in votos.items()), key=lambda c: -c["votos"])
    tot["secoes_pct"] = tot["secoes"] / tot["secoes_total"] * 100
    return tot


def resumos_coleta(pasta):
    """{UF: resumo} de uma pasta bruta, só se estiver completa."""
    out = {}
    for uf in NOMES:
        u = ler_json(pasta / f"{uf.lower()}-u.json")
        if not u:
            return None
        out[uf] = resumo_tse(u)
    return out


def projecao(por_uf):
    """Cada UF termina com o placar atual dela; votos escalados pelo que falta apurar.

    por_uf: {uf: (fração_apurada, votos_flavio, votos_lula, votos_validos)}
    """
    pf = pl = pv = 0.0
    for frac, vf, vl, vv in por_uf.values():
        if frac <= 0 or vv <= 0:
            continue
        pf += vf / frac
        pl += vl / frac
        pv += vv / frac
    if not pv:
        return None
    return {"flavio": pf / pv * 100, "lula": pl / pv * 100}


def main():
    brutos = sorted((PASTA / "brutos").glob("*/br-u.json"))
    if not brutos:
        print("painel: nenhuma coleta do TSE ainda")
        return
    ultima = brutos[-1].parent
    u_br = ler_json(ultima / "br-u.json")
    res_ultima = resumos_coleta(ultima)
    br = somar(res_ultima.values()) if res_ultima else resumo_tse(u_br)
    atualizado = f"{ultima.name[6:8]}/{ultima.name[4:6]} {ultima.name[9:11]}:{ultima.name[11:13]} (soma dos estados)"

    # ---- estados (coleta mais recente) ----
    ufs = []
    for uf in NOMES:
        u = ler_json(ultima / f"{uf.lower()}-u.json")
        if not u:
            continue
        r = resumo_tse(u)
        por_num = {c["num"]: c for c in r["cands"]}
        fl, lu = por_num.get("22"), por_num.get("13")
        ufs.append({
            "uf": uf, "nome": NOMES[uf], "regiao": REGIAO_DE[uf],
            "secoes_pct": r["secoes_pct"], "eleitorado": r["eleitorado"],
            "restante": r["eleitorado"] - r["eleitorado_apurado"],
            "frac": r["eleitorado_apurado"] / r["eleitorado"] if r["eleitorado"] else 0,
            "flavio": fl["pct"] if fl else None, "lula": lu["pct"] if lu else None,
            "vf": fl["votos"] if fl else 0, "vl": lu["votos"] if lu else 0, "validos": r["validos"],
        })

    regioes = []
    for nome, lista in REGIOES.items():
        sel = [x for x in ufs if x["uf"] in lista]
        te = sum(x["eleitorado"] for x in sel)
        rest = sum(x["restante"] for x in sel)
        vv = sum(x["validos"] for x in sel)
        regioes.append({
            "nome": nome, "eleitorado": te, "restante": rest,
            "pct": (te - rest) / te * 100 if te else 0,
            "flavio": sum(x["vf"] for x in sel) / vv * 100 if vv else None,
            "lula": sum(x["vl"] for x in sel) / vv * 100 if vv else None,
        })

    proj_atual = projecao({x["uf"]: (x["frac"], x["vf"], x["vl"], x["validos"]) for x in ufs if x["uf"] != "BR"})

    # ---- quanto o Flávio precisa nos válidos restantes para passar de 50% ----
    fl_br = next(c for c in br["cands"] if c["num"] == "22")
    frac_br = br["eleitorado_apurado"] / br["eleitorado"]
    validos_final = br["validos"] / frac_br if frac_br else 0
    faltam = validos_final - br["validos"]
    precisa = (validos_final / 2 - fl_br["votos"]) / faltam * 100 if faltam > 0 else None

    # ---- histórico + lotes: recalculados de cada coleta bruta ----
    historico, lotes, ant = [], [], None
    for arq in brutos:
        res = resumos_coleta(arq.parent)
        if not res:
            continue
        h = f"{arq.parent.name[9:11]}:{arq.parent.name[11:13]}"
        nac = somar(res.values())
        c0 = {c["num"]: c for c in nac["cands"]}
        por_uf = {}
        for uf, r in res.items():
            num = {c["num"]: c["votos"] for c in r["cands"]}
            frac = r["eleitorado_apurado"] / r["eleitorado"] if r["eleitorado"] else 0
            por_uf[uf] = (frac, num.get("22", 0), num.get("13", 0), r["validos"])
        p = projecao(por_uf)
        if p:
            historico.append({"h": h, "urnas": nac["secoes_pct"], "proj_f": p["flavio"], "proj_l": p["lula"],
                              "real_f": c0["22"]["pct"], "real_l": c0["13"]["pct"]})
        atual = {"BR": (c0["22"]["votos"], c0["13"]["votos"], nac["validos"], nac["secoes_pct"])}
        for uf, (frac, vf, vl, vv) in por_uf.items():
            atual[uf] = (vf, vl, vv, res[uf]["secoes_pct"])
        if ant:
            lote = {"h": h, "de": ant[0], "ufs": {}}
            for k, (vf, vl, vv, sec) in atual.items():
                af, al, avv, asec = ant[1][k]
                dv = vv - avv
                if dv <= 0:
                    continue
                reg = {"f": vf - af, "l": vl - al, "o": dv - (vf - af) - (vl - al), "v": dv,
                       "sec0": asec, "sec1": sec, "pf_antes": af / avv * 100 if avv else None,
                       "pl_antes": al / avv * 100 if avv else None}
                if k == "BR":
                    lote.update(reg)
                else:
                    lote["ufs"][k] = reg
            if "v" in lote:
                lotes.append(lote)
        ant = (h, atual)

    # ---- evolução 2026 x 2022 (UOL); se faltar, usa nossos snapshots ----
    snaps = {l["horario"]: l for l in ler_csv("snapshots.csv")}
    ev26, ev22 = [], []
    uol26 = ler_json(PASTA / "uol-evolucao-2026.json")
    if uol26:
        for p in uol26.get("evol", []):
            c = {x["num"]: x["vp"] for x in p["ca"]}
            if 22 in c and 13 in c:
                ev26.append([p["sap"], c[22], c[13]])
    # completa com o nosso histórico (soma das UFs), que vai além da série do UOL
    ev26 += [[h["urnas"], h["real_f"], h["real_l"]] for h in historico]
    ev26.sort(key=lambda p: p[0])
    uol22 = ler_json(PASTA / "uol-historico-2022.json")
    if uol22:
        i = uol22["tuple"]
        il, ib = i.index("candidate13Percent"), i.index("candidate22Percent")
        ev22 = [[p[0], p[ib], p[il]] for p in uol22["series"]]  # [urnas, bolsonaro, lula]

    dados = {
        "atualizado": atualizado, "pasta": ultima.name,
        "br": br, "ufs": ufs, "regioes": regioes,
        "projecao": proj_atual, "precisa": precisa,
        "historico": historico, "lotes": lotes, "ev26": ev26, "ev22": ev22,
        "n_coletas": len(snaps),
    }
    topo = (PASTA / "br-estados.topo.json").read_text(encoding="utf-8")
    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("/*__DADOS__*/null", json.dumps(dados, ensure_ascii=False))
    html = html.replace("/*__TOPO__*/null", topo)
    SAIDA.write_text(html, encoding="utf-8")
    print(f"painel: {SAIDA.name} atualizado (TSE {atualizado})")


if __name__ == "__main__":
    main()
