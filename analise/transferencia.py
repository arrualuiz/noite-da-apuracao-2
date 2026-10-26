#!/usr/bin/env python3
"""Em pessoas: quem foi votar, quem deixou de ir, e para onde foram os eleitores de cada candidato do 1º turno.

1. Contas do Brasil, em % e em pessoas: 1º turno (final) x 2º turno (seções apuradas, levado a 100%
   pelo mesmo % do eleitorado).
2. Transferência de votos estimada por regressão de Goodman (inferência ecológica): em cada cidade
   100% apurada, a parte do eleitorado que foi para Lula, Flávio, branco/nulo e abstenção no 2º turno
   é explicada pela parte que votou em cada opção no 1º turno. Mínimos quadrados ponderados pelo
   eleitorado, sem intercepto, com a restrição de que cada linha fica entre 0 e 100% e soma 100%
   (gradiente projetado). Sem a restrição, a regressão dá valores impossíveis (ex.: -77%).
   É uma estimativa: supõe que os eleitores de um candidato se comportam igual em todas as cidades.

Grava a tabela da parte 2 em dados/transferencia.csv.

Uso: python3 analise/abstencao.py && python3 analise/transferencia.py
"""
import csv
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "dados"
PASTA_1T = PASTA / "historico" / "tse" / "1t-municipios"
ORIGENS = ["Lula", "Flávio", "Cury", "Renan", "Caiado", "Demais candidatos", "Branco/nulo", "Abstenção"]
DESTINOS = ["Lula", "Flávio", "Branco/nulo", "Abstenção"]
NUM_1T = {"13": "Lula", "22": "Flávio", "70": "Cury", "14": "Renan", "55": "Caiado"}


def mil(n):
    return f"{n:,.0f}".replace(",", ".")


def ler(arq, segundo_turno):
    u = json.loads(arq.read_text(encoding="utf-8"))
    e, v = u["e"], u["v"]
    c = {x["n"]: int(x["vap"]) for a in u["carg"][0]["agr"] for p in a["par"] for x in p["cand"]}
    bn = int(v["vb"]) + int(v["tvn"])
    out = {"te": int(e["te"]), "est": int(e["est"]), "Branco/nulo": bn, "Abstenção": int(e["a"]),
           "Comparecimento": int(e["c"]), "Brancos": int(v["vb"]), "Nulos": int(v["tvn"])}
    if segundo_turno:
        out.update({"Lula": c.get("13", 0), "Flávio": c.get("22", 0)})
    else:
        for o in ORIGENS[:5]:
            out[o] = 0
        out["Demais candidatos"] = 0
        for n, votos in c.items():
            out[NUM_1T.get(n, "Demais candidatos")] += votos
    return out


def resolver(A, b):
    """Resolve A x = b (eliminação de Gauss com pivô parcial)."""
    n = len(A)
    M = [A[i][:] + [b[i]] for i in range(n)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        M[col], M[piv] = M[piv], M[col]
        for r in range(n):
            if r != col and M[col][col]:
                f = M[r][col] / M[col][col]
                M[r] = [a - f * c for a, c in zip(M[r], M[col])]
    return [M[i][n] / M[i][i] for i in range(n)]


def projetar_simplex(v):
    """Projeta um vetor no conjunto {x >= 0, soma = 1}."""
    u = sorted(v, reverse=True)
    acum, theta = 0.0, 0.0
    for i, ui in enumerate(u, 1):
        acum += ui
        t = (acum - 1) / i
        if ui - t > 0:
            theta = t
    return [max(x - theta, 0) for x in v]


def goodman_restrito(XtWX, XtWY, passos=20000):
    """min tr(B'AB) - 2 tr(B'C), cada linha de B no simplex (gradiente projetado)."""
    k, d = len(XtWX), len(XtWY[0])
    # maior autovalor de A (potência) para o tamanho do passo
    v = [1.0] * k
    for _ in range(200):
        w = [sum(XtWX[i][j] * v[j] for j in range(k)) for i in range(k)]
        n = max(abs(x) for x in w)
        v = [x / n for x in w]
    passo = 1 / (2 * n)
    B = [[1 / d] * d for _ in range(k)]
    for _ in range(passos):
        AB = [[sum(XtWX[i][m] * B[m][j] for m in range(k)) for j in range(d)] for i in range(k)]
        B = [projetar_simplex([B[i][j] - passo * 2 * (AB[i][j] - XtWY[i][j]) for j in range(d)]) for i in range(k)]
    return B


def main():
    pasta_2t = max((d / "todos-mun" for d in (PASTA / "brutos").iterdir() if (d / "todos-mun").exists()),
                   key=lambda p: p.parent.name)
    br1 = json.loads(sorted((RAIZ.parent / "xx-noite-do-primeiro-turno-2026" / "dados" / "brutos").glob("*/br-u.json"))[-1]
                     .read_text(encoding="utf-8"))
    ultima = sorted(d for d in (PASTA / "brutos").iterdir() if (d / "br-u.json").exists())[-1]
    br2 = json.loads((ultima / "br-u.json").read_text(encoding="utf-8"))

    # 1. contas do Brasil
    def contas(u):
        e, v = u["e"], u["v"]
        c, a = int(e["c"]), int(e["a"])
        return {"te": int(e["te"]), "c": c, "a": a, "vb": int(v["vb"]), "vn": int(v["tvn"]), "vv": int(v["vv"])}
    t1, t2 = contas(br1), contas(br2)
    fator = t2["te"] / (t2["c"] + t2["a"])  # leva as seções apuradas ao eleitorado inteiro
    secoes = br2["s"]["pstn"].replace(",", ".")
    print(f"1. BRASIL EM PESSOAS · 2º turno com {float(secoes):.1f}% das seções, levado a 100% ({ultima.name[9:11]}:{ultima.name[11:13]})\n")
    print(f"   {'':16}{'1º turno':>24}{'2º turno (a 100%)':>26}{'diferença':>24}")
    for nome, k, base in (("Foram votar", "c", None), ("Não foram", "a", None), ("Brancos", "vb", "c"), ("Nulos", "vn", "c")):
        p1 = t1[k] / (t1[base] if base else t1["c"] + t1["a"]) * 100
        p2 = t2[k] / (t2[base] if base else t2["c"] + t2["a"]) * 100
        n1, n2 = t1[k], t2[k] * fator
        print(f"   {nome:16}{mil(n1):>13} ({p1:5.2f}%){mil(n2):>15} ({p2:5.2f}%){mil(n2 - n1):>13} ({p2 - p1:+.2f} pts)")
    print("   (brancos e nulos: % de quem foi votar)")

    # 2. regressão de Goodman nas cidades 100% apuradas
    cfg = json.loads((PASTA / "municipios-6258.json").read_text(encoding="utf-8"))
    X, Y, W = [], [], []
    for a in cfg["abr"]:
        if a["cd"] == "zz":
            continue
        for m in a["mu"]:
            f1, f2 = PASTA_1T / f"{a['cd']}{m['cd']}.json", pasta_2t / f"{a['cd']}{m['cd']}.json"
            if not (f1.exists() and f2.exists()):
                continue
            x1, x2 = ler(f1, False), ler(f2, True)
            if x2["est"] < x2["te"] or not x1["te"] or not x2["te"]:
                continue
            X.append([x1[o] / x1["te"] for o in ORIGENS])
            Y.append([x2[d] / x2["te"] for d in DESTINOS])
            W.append(x2["te"])
    k = len(ORIGENS)
    XtWX = [[sum(w * x[i] * x[j] for x, w in zip(X, W)) for j in range(k)] for i in range(k)]
    XtWY = [[sum(w * x[i] * y[d] for x, y, w in zip(X, Y, W)) for d in range(len(DESTINOS))] for i in range(k)]
    livre = {nome: resolver(XtWX, [XtWY[i][d] for i in range(k)]) for d, nome in enumerate(DESTINOS)}
    B = goodman_restrito(XtWX, XtWY)
    coef = {nome: [B[i][d] for i in range(k)] for d, nome in enumerate(DESTINOS)}
    fora = sum(1 for nome in DESTINOS for c in livre[nome] if c < -0.01 or c > 1.01)

    tot1 = ler_brasil_1t(br1)
    print(f"\n2. PARA ONDE FOI QUEM VOTOU EM CADA UM NO 1º TURNO (estimativa; {len(X)} cidades 100% apuradas)\n")
    print(f"   {'1º turno':20}{'eleitores':>12}" + "".join(f"{d:>22}" for d in DESTINOS))
    for i, o in enumerate(ORIGENS):
        linha = f"   {o:20}{mil(tot1[o]):>12}"
        for d in DESTINOS:
            c = coef[d][i]
            linha += f"{mil(c * tot1[o]):>12} ({c * 100:5.1f}%)"
        print(linha)
    with (PASTA / "transferencia.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["origem", "eleitores_1t", "destino", "pct", "pessoas"])
        for i, o in enumerate(ORIGENS):
            for d in DESTINOS:
                w.writerow([o, tot1[o], d, round(coef[d][i] * 100, 2), round(coef[d][i] * tot1[o])])
    print(f"\n   Sem a restrição, {fora} dos {len(ORIGENS) * len(DESTINOS)} coeficientes saíam abaixo de 0% ou acima de 100%.")
    print("\n   Lê-se assim: de cada 100 eleitores do Cury no 1º turno, a coluna mostra quantos foram para o Lula,")
    print("   para o Flávio, votaram branco/nulo ou não foram votar no 2º. Os números em pessoas são essa")
    print("   estimativa aplicada ao total de eleitores de cada um no Brasil.")


def ler_brasil_1t(u):
    e, v = u["e"], u["v"]
    out = {o: 0 for o in ORIGENS}
    for a in u["carg"][0]["agr"]:
        for p in a["par"]:
            for c in p["cand"]:
                out[NUM_1T.get(c["n"], "Demais candidatos")] += int(c["vap"])
    out["Branco/nulo"] = int(v["vb"]) + int(v["tvn"])
    out["Abstenção"] = int(e["a"])
    return out


if __name__ == "__main__":
    main()
