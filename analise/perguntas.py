#!/usr/bin/env python3
"""As perguntas da noite, recalculadas a cada coleta, e a previsão do resultado final.

Perguntas:
  1. Para onde foram os votos de quem não votou em Lula nem em Flávio no 1º turno?
  2. Quem ganha Minas?
  3. Algum estado do Sul mudou de lado entre o 1º e o 2º turno?
  +  Nordeste: Lula e Flávio cresceram em votos?
  +  O comparecimento mudou do 1º para o 2º turno?

Previsão: para o que falta apurar em cada estado, mistura o que o estado já mostrou no 2º turno
com o 1º turno do estado corrigido pelo ganho médio do Lula na região. Quanto mais apurado,
mais pesa o que o estado já mostrou (peso = apurado / (apurado + 10%)).

Gera:
  dados/previsao.csv       uma linha por coleta (placar, previsão, Minas, comparecimento)
  dados/perguntas_uf.csv   a situação de cada estado na última coleta
  painel/perguntas.html    o painel das perguntas

Uso: python3 analise/perguntas.py   (o coletar.py chama isto a cada coleta)
"""
import csv
import json
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "dados"
BRUTOS = PASTA / "brutos"
SAIDA_HTML = RAIZ / "painel" / "perguntas.html"
TEMPLATE = RAIZ / "painel" / "perguntas-template.html"

REGIOES = {
    "Norte": ["AC", "AM", "AP", "PA", "RO", "RR", "TO"],
    "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Centro-Oeste": ["DF", "GO", "MS", "MT"],
    "Sudeste": ["ES", "MG", "RJ", "SP"],
    "Sul": ["PR", "RS", "SC"],
    "Exterior": ["ZZ"],
}
REGIAO = {uf: r for r, ufs in REGIOES.items() for uf in ufs}
NOMES = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão", "MG": "Minas Gerais",
    "MS": "Mato Grosso do Sul", "MT": "Mato Grosso", "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco",
    "PI": "Piauí", "PR": "Paraná", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RO": "Rondônia",
    "RR": "Roraima", "RS": "Rio Grande do Sul", "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo",
    "TO": "Tocantins", "ZZ": "Exterior",
}
MEIA_CONFIANCA = 0.10  # com 10% apurado, o estado e o 1º turno pesam igual
# Erro da projeção por estado na diferença entre os dois primeiros (pontos), medido no 1º turno de 2026
# (noite-do-primeiro-turno-2026, dados/export/nacional.csv x resultado final). Antes dos 25%, não há medida.
ERRO_1T = [(0, 6.0), (25, 4.1), (30, 3.3), (40, 2.6), (50, 2.2), (60, 1.5), (70, 1.4), (80, 1.05),
           (90, 0.72), (95, 0.46), (99, 0.17), (100, 0.0)]


def erro_esperado(secoes):
    """Erro típico da previsão neste ponto da apuração, interpolado da tabela do 1º turno."""
    for (x0, e0), (x1, e1) in zip(ERRO_1T, ERRO_1T[1:]):
        if secoes <= x1:
            return e0 + (e1 - e0) * (secoes - x0) / (x1 - x0)
    return 0.0


def ler_1t():
    t1 = {}
    for r in csv.DictReader((PASTA / "historico" / "2026-t1-uf.csv").open(encoding="utf-8")):
        n = {k: int(r[k]) for k in ("eleitorado", "comparecimento", "abstencao", "validos", "lula", "flavio", "outros")}
        t1[r["uf"]] = n
    return t1


def ler_2022():
    """Lula e Bolsonaro no 2º turno de 2022, por UF."""
    v = {}
    for r in csv.DictReader((PASTA / "historico" / "presidente_votos_uf.csv").open(encoding="utf-8")):
        if r["ano"] == "2022" and r["turno"] == "2" and r["numero"] in ("13", "22"):
            v.setdefault(r["uf"], {})[r["numero"]] = int(r["votos"])
    return v


def ler_coleta(pasta):
    ufs = {}
    for uf in NOMES:
        u = json.loads((pasta / f"{uf.lower()}-u.json").read_text(encoding="utf-8"))
        c = {x["n"]: int(x["vap"]) for a in u["carg"][0]["agr"] for p in a["par"] for x in p["cand"]}
        e, v = u["e"], u["v"]
        ufs[uf] = {"l": c.get("13", 0), "f": c.get("22", 0), "te": int(e["te"]), "est": int(e["est"]),
                   "c": int(e["c"]), "a": int(e["a"]), "vv": int(v["vv"])}
    br = json.loads((pasta / "br-u.json").read_text(encoding="utf-8"))
    return ufs, {"secoes": float(br["s"]["pstn"].replace(",", ".")), "versao": f"{br['dg']} {br['hg']}",
                 "md": br.get("md"), "tf": br.get("tf")}


def ganho_lula(ufs, t1, lista):
    """Ganho médio do Lula sobre a parte dele em Lula + Flávio no 1º turno, ponderado pelos votos já apurados."""
    num = den = 0
    for uf in lista:
        x = ufs[uf]
        n = x["l"] + x["f"]
        if n:
            s1 = t1[uf]["lula"] / (t1[uf]["lula"] + t1[uf]["flavio"])
            num += (x["l"] / n - s1) * n
            den += n
    return (num / den if den else 0.0), den


def calcular(pasta, t1):
    ufs, br = ler_coleta(pasta)
    no_brasil = [uf for uf in NOMES if uf != "ZZ"]
    g_nac, _ = ganho_lula(ufs, t1, no_brasil)
    estados = {}
    for uf, x in ufs.items():
        a = t1[uf]
        frac = x["est"] / x["te"] if x["te"] else 0
        w = frac / (frac + MEIA_CONFIANCA)
        # ganho da região se ela já tem votos suficientes; senão, o nacional
        g_reg, n_reg = ganho_lula(ufs, t1, REGIOES[REGIAO[uf]])
        g = g_reg if n_reg >= 200_000 else g_nac
        s1 = a["lula"] / (a["lula"] + a["flavio"])
        n = x["l"] + x["f"]
        s_obs = x["l"] / n if n else s1
        s = w * s_obs + (1 - w) * min(max(s1 + g, 0), 1)
        # quantos votos válidos ainda faltam: eleitorado não apurado x comparecimento x % de válidos
        comp1, val1 = a["comparecimento"] / a["eleitorado"], a["validos"] / a["comparecimento"]
        comp_obs = x["c"] / (x["c"] + x["a"]) if x["c"] + x["a"] else comp1
        val_obs = x["vv"] / x["c"] if x["c"] else val1
        comp = w * comp_obs + (1 - w) * comp1
        val = w * val_obs + (1 - w) * val1
        resto = max(x["te"] - x["est"], 0) * comp * val
        pl, pf = x["l"] + resto * s, x["f"] + resto * (1 - s)
        # parte dos votos dos outros candidatos do 1º turno que foi para o Lula (supondo que ninguém trocou de lado)
        p_l, p_o = a["lula"] / a["validos"], a["outros"] / a["validos"]
        estados[uf] = {
            "uf": uf, "nome": NOMES[uf], "regiao": REGIAO[uf], "apurado": round(frac * 100, 2),
            "lula": x["l"], "flavio": x["f"], "pct_lula": round(s_obs * 100, 2) if n else None,
            "pct_lula_1t": round(s1 * 100, 2),
            "ganho_lula": round((s_obs - s1) * 100, 2) if n else None,
            "outros_para_lula": round((s_obs - p_l) / p_o * 100, 1) if n and p_o else None,
            "prev_lula": round(pl), "prev_flavio": round(pf), "prev_pct_lula": round(pl / (pl + pf) * 100, 2),
            "lula_1t": a["lula"], "flavio_1t": a["flavio"], "outros_1t": a["outros"],
            "comparecimento": round(comp_obs * 100, 2) if x["c"] + x["a"] else None,
            "comparecimento_1t": round(comp1 * 100, 2),
        }
    return br, estados, g_nac


def somar(estados, lista):
    s = {k: sum(estados[uf][k] for uf in lista) for k in ("lula", "flavio", "prev_lula", "prev_flavio",
                                                          "lula_1t", "flavio_1t", "outros_1t")}
    s["prev_pct_lula"] = round(s["prev_lula"] / (s["prev_lula"] + s["prev_flavio"]) * 100, 2)
    n = s["lula"] + s["flavio"]
    s["pct_lula"] = round(s["lula"] / n * 100, 2) if n else None
    return s


def comparecimento(pasta, lista, t1):
    """Comparecimento nas seções já apuradas x 1º turno inteiro, para um grupo de UFs."""
    ufs, _ = ler_coleta(pasta)
    c = sum(ufs[u]["c"] for u in lista)
    a = sum(ufs[u]["a"] for u in lista)
    c1 = sum(t1[u]["comparecimento"] for u in lista)
    e1 = sum(t1[u]["eleitorado"] for u in lista)
    return (round(c / (c + a) * 100, 2) if c + a else None), round(c1 / e1 * 100, 2)


def main():
    t1, v22 = ler_1t(), ler_2022()
    coletas = sorted(d for d in BRUTOS.iterdir() if (d / "br-u.json").exists())
    linhas, validas = [], []
    for pasta in coletas:
        try:
            br, est, g = calcular(pasta, t1)
        except (OSError, KeyError, ValueError, json.JSONDecodeError):  # coleta incompleta
            continue
        validas.append(pasta)
        tot = somar(est, list(NOMES))
        mg = est["MG"]
        comp, comp1 = comparecimento(pasta, [u for u in NOMES if u != "ZZ"], t1)
        linhas.append({
            "horario": datetime.strptime(pasta.name, "%Y%m%d-%H%M%S").strftime("%Y-%m-%d %H:%M:%S"),
            "coleta_id": pasta.name, "secoes_pct": br["secoes"],
            "pct_lula": tot["pct_lula"], "prev_pct_lula": tot["prev_pct_lula"],
            "prev_dif_votos": tot["prev_lula"] - tot["prev_flavio"], "ganho_lula": round(g * 100, 2),
            "mg_apurado": mg["apurado"], "mg_pct_lula": mg["pct_lula"], "mg_prev_pct_lula": mg["prev_pct_lula"],
            "comparecimento": comp, "comparecimento_1t": comp1,
        })
    if not linhas:
        return
    with (PASTA / "previsao.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)

    ultima = validas[-1]
    br, est, g = calcular(ultima, t1)
    with (PASTA / "perguntas_uf.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(est["MG"]))
        w.writeheader()
        w.writerows(est.values())

    regioes = {}
    for r, lista in REGIOES.items():
        s = somar(est, lista)
        s["comparecimento"], s["comparecimento_1t"] = comparecimento(ultima, lista, t1) if r != "Exterior" else (None, None)
        regioes[r] = s
    dados = {
        "gerado": datetime.now().strftime("%d/%m %H:%M:%S"), "versao_tse": br["versao"], "secoes": br["secoes"],
        "md": br["md"], "tf": br["tf"], "ganho_lula": round(g * 100, 2),
        "total": somar(est, list(NOMES)), "erro_esperado": round(erro_esperado(br["secoes"]), 2), "estados": est, "regioes": regioes, "serie": linhas,
        "v2022": {uf: {"lula": v.get("13", 0), "bolsonaro": v.get("22", 0)} for uf, v in v22.items()},
        "palpites": list(csv.DictReader((PASTA / "palpites.csv").open(encoding="utf-8"))),
    }
    html = TEMPLATE.read_text(encoding="utf-8").replace("/*DADOS*/null", json.dumps(dados, ensure_ascii=False))
    SAIDA_HTML.write_text(html, encoding="utf-8")
    t = dados["total"]
    print(f"perguntas: {br['secoes']:.2f}% | placar Lula {t['pct_lula']}% | previsão Lula {t['prev_pct_lula']}% "
          f"| MG previsão {est['MG']['prev_pct_lula']}%")


if __name__ == "__main__":
    main()
