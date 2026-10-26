#!/usr/bin/env python3
"""Olhando para trás: a previsão da noite errou onde, e outro método teria acertado antes?

Com o resultado final em mãos, refaz a previsão em cada coleta da noite com quatro métodos e mede
o erro de cada um no % do Lula (entre Lula e Flávio):
  - placar:        o que já estava apurado, sem previsão nenhuma;
  - modelo:        o da noite (analise/perguntas.py), com o peso apurado / (apurado + 10%);
  - modelo peso X: o mesmo modelo com outros pesos (2%, 25%), para ver se o 10% foi um bom chute;
  - mesmo ponto:   em cada estado, a diferença entre o 2º turno e o 1º turno no MESMO % apurado
                   (coletas brutas de noite-do-primeiro-turno-2026), somada ao 1º turno final do estado.
                   Isso tira o efeito da ordem de apuração (as primeiras seções de cada estado não
                   são iguais às últimas, e a ordem se repete de um turno para o outro).
Depois mostra, num ponto do meio da noite, de quais estados veio o erro do modelo, em votos.

Uso: python3 analise/retroativo.py
"""
import bisect
import json
from datetime import datetime
from pathlib import Path

import perguntas as P

RAIZ = Path(__file__).resolve().parent.parent
BRUTOS_1T = RAIZ.parent / "xx-noite-do-primeiro-turno-2026" / "dados" / "brutos"
MARCOS = [5, 10, 20, 30, 40, 50, 60, 70, 80, 90]


def mil(n):
    return f"{n:,.0f}".replace(",", ".")


def lf(pasta, uf):
    u = json.loads((pasta / f"{uf.lower()}-u.json").read_text(encoding="utf-8"))
    c = {x["n"]: int(x["vap"]) for a in u["carg"][0]["agr"] for p in a["par"] for x in p["cand"]}
    return int(u["e"]["est"]) / int(u["e"]["te"]), c.get("13", 0), c.get("22", 0)


def curvas_1t():
    """Para cada UF, a curva (fração apurada, % do Lula entre Lula e Flávio) da noite do 1º turno."""
    curvas = {uf: [] for uf in P.NOMES}
    for pasta in sorted(d for d in BRUTOS_1T.iterdir() if (d / "br-u.json").exists()):
        for uf in P.NOMES:
            frac, l, f = lf(pasta, uf)
            if l + f and (not curvas[uf] or frac > curvas[uf][-1][0]):
                curvas[uf].append((frac, l / (l + f)))
    return curvas


def no_ponto(curva, frac):
    """% do Lula no 1º turno quando a UF estava com a mesma fração apurada (interpolação linear)."""
    xs = [c[0] for c in curva]
    i = bisect.bisect_left(xs, frac)
    if i == 0:
        return curva[0][1]
    if i == len(curva):
        return curva[-1][1]
    (x0, y0), (x1, y1) = curva[i - 1], curva[i]
    return y0 + (y1 - y0) * (frac - x0) / (x1 - x0)


def mesmo_ponto(pasta, t1, curvas):
    ufs, _ = P.ler_coleta(pasta)
    swing, tot, est = {}, {}, {}
    for uf, x in ufs.items():
        a = t1[uf]
        s1 = a["lula"] / (a["lula"] + a["flavio"])
        frac, n = x["est"] / x["te"], x["l"] + x["f"]
        if n and frac > 0.005:
            swing[uf] = x["l"] / n - no_ponto(curvas[uf], frac)
            tot[uf] = n
    g = sum(swing[u] * tot[u] for u in swing) / sum(tot.values())  # quem ainda não tem voto usa a média
    L = F = 0
    for uf, x in ufs.items():
        a = t1[uf]
        s1 = a["lula"] / (a["lula"] + a["flavio"])
        s = min(max(s1 + swing.get(uf, g), 0), 1)
        frac = x["est"] / x["te"]
        n_final = a["validos"] * (1 - frac) + (x["l"] + x["f"]) if frac < 1 else x["l"] + x["f"]
        resto = max(n_final - x["l"] - x["f"], 0)
        # o que falta tem o % que faz o estado fechar em s
        s_resto = min(max((s * n_final - x["l"]) / resto, 0), 1) if resto else 0
        L += x["l"] + resto * s_resto
        F += x["f"] + resto * (1 - s_resto)
    return L / (L + F) * 100


def modelo(pasta, t1, peso):
    P.MEIA_CONFIANCA = peso
    _, estados, _ = P.calcular(pasta, t1)
    return P.somar(estados, list(P.NOMES))["prev_pct_lula"], estados


def main():
    t1 = P.ler_1t()
    curvas = curvas_1t()
    coletas = sorted(d for d in P.BRUTOS.iterdir() if (d / "br-u.json").exists())
    ufs_fim, br_fim = P.ler_coleta(coletas[-1])
    L, F = sum(x["l"] for x in ufs_fim.values()), sum(x["f"] for x in ufs_fim.values())
    final = L / (L + F) * 100
    print(f"Resultado final (coleta {coletas[-1].name[9:11]}:{coletas[-1].name[11:13]}, {br_fim['secoes']:.2f}%): "
          f"Lula {final:.2f}%\n")

    linhas, vistos = [], set()
    for pasta in coletas:
        ufs, br = P.ler_coleta(pasta)
        m = next((m for m in MARCOS if br["secoes"] >= m and m not in vistos), None)
        if m is None:
            continue
        vistos.add(m)
        l, f = sum(x["l"] for x in ufs.values()), sum(x["f"] for x in ufs.values())
        linhas.append((pasta, br["secoes"], {
            "placar": l / (l + f) * 100,
            "modelo (10%)": modelo(pasta, t1, 0.10)[0],
            "peso 2%": modelo(pasta, t1, 0.02)[0],
            "peso 25%": modelo(pasta, t1, 0.25)[0],
            "mesmo ponto": mesmo_ponto(pasta, t1, curvas),
        }))
    nomes = list(linhas[0][2])
    print("ERRO DE CADA MÉTODO NO % DO LULA (previsto - final, em pontos)\n")
    print(f"  {'hora':5} {'seções':>7}" + "".join(f"{n:>14}" for n in nomes))
    for pasta, sec, r in linhas:
        print(f"  {pasta.name[9:11]}:{pasta.name[11:13]} {sec:6.1f}%" + "".join(f"{r[n] - final:+14.2f}" for n in nomes))
    print(f"\n  {'média |erro|':13}" + "".join(f"{sum(abs(r[n] - final) for _, _, r in linhas) / len(linhas):14.2f}" for n in nomes))
    print("\n  Negativo = previa menos Lula do que deu. Em pessoas, 1 ponto ≈ "
          f"{mil((L + F) / 100)} votos.")

    # de onde veio o erro do modelo no meio da noite
    pasta, sec, _ = next(x for x in linhas if x[1] >= 30)
    _, est = modelo(pasta, t1, 0.10)
    print(f"\nDE ONDE VEIO O ERRO DO MODELO ÀS {pasta.name[9:11]}:{pasta.name[11:13]} ({sec:.1f}% das seções)")
    print("  Diferença Lula - Flávio prevista para o estado x a final, em votos (negativo = previa menos Lula)\n")
    erros = []
    for uf, e in est.items():
        x = ufs_fim[uf]
        erros.append(((e["prev_lula"] - e["prev_flavio"]) - (x["l"] - x["f"]), uf, e))
    total = sum(e[0] for e in erros)
    for err, uf, e in sorted(erros)[:8]:
        x = ufs_fim[uf]
        print(f"  {e['nome']:20} apurado {e['apurado']:5.1f}%  previa Lula {e['prev_pct_lula']:5.2f}%"
              f"  deu {x['l'] / (x['l'] + x['f']) * 100:5.2f}%  erro {mil(err):>10} votos")
    print(f"  {'Brasil':20} erro total {mil(total)} votos na diferença")
    P.MEIA_CONFIANCA = 0.10


if __name__ == "__main__":
    main()
