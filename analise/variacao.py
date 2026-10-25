#!/usr/bin/env python3
"""O que mudou em cada estado entre duas leituras, e quanto o que falta ainda pesa.

Uso:
  python3 analise/variacao.py                 # compara as duas últimas coletas
  python3 analise/variacao.py 18:48 19:14     # compara as coletas mais próximas desses horários
  python3 analise/variacao.py --todas UF      # evolução de um estado em todas as coletas (ex.: SP)
"""
import json
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent / "dados" / "brutos"
UFS = ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB",
       "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO", "ZZ"]


def br(n):
    return f"{n:,.0f}".replace(",", ".")


def ler(pasta, uf):
    """Votos de Flávio/Lula, válidos e fração apurada de uma UF numa coleta."""
    u = json.loads((pasta / f"{uf.lower()}-u.json").read_text(encoding="utf-8"))
    c = {x["n"]: int(x["vap"]) for a in u["carg"][0]["agr"] for p in a["par"] for x in p["cand"]}
    te, est = int(u["e"]["te"]), int(u["e"]["est"])
    return {"f": c.get("22", 0), "l": c.get("13", 0), "vv": int(u["v"]["vv"]),
            "frac": est / te if te else 0, "secoes": float(u["s"]["pstn"].replace(",", ".")),
            "versao": f"{u['dg']} {u['hg']}"}


def coletas():
    return sorted(d for d in PASTA.iterdir() if (d / "br-u.json").exists())


def hora(pasta):
    return f"{pasta.name[9:11]}:{pasta.name[11:13]}"


def achar(hhmm, lista):
    alvo = int(hhmm[:2]) * 60 + int(hhmm[3:5])
    return min(lista, key=lambda d: abs(int(d.name[9:11]) * 60 + int(d.name[11:13]) - alvo))


def restante_validos(x):
    return x["vv"] / x["frac"] - x["vv"] if x["frac"] > 0 else 0


def comparar(a, b):
    print(f"Comparando coleta {hora(a)} → {hora(b)}\n")
    linhas = []
    for uf in UFS:
        x, y = ler(a, uf), ler(b, uf)
        dv, df, dl = y["vv"] - x["vv"], y["f"] - x["f"], y["l"] - x["l"]
        pf_acum = y["f"] / y["vv"] * 100 if y["vv"] else 0
        pl_acum = y["l"] / y["vv"] * 100 if y["vv"] else 0
        rest = restante_validos(y)
        saldo = rest * (pf_acum - pl_acum) / 100  # + = Flávio ganha, − = Lula ganha
        linhas.append({
            "uf": uf, "ap0": x["secoes"], "ap1": y["secoes"], "dv": dv,
            "pf_lote": df / dv * 100 if dv > 0 else None, "pl_lote": dl / dv * 100 if dv > 0 else None,
            "pf": pf_acum, "pl": pl_acum, "rest": rest, "saldo": saldo,
        })

    print("1) O QUE ENTROU NESSE INTERVALO (estados com votos novos, maior lote primeiro)")
    print(f"{'UF':<4}{'apurado':>15}{'válidos novos':>15}{'lote F x L':>15}{'acum F x L':>15}  tendência do lote")
    for r in sorted([r for r in linhas if r["dv"] > 0], key=lambda r: -r["dv"]):
        lote_dif = r["pf_lote"] - r["pl_lote"]
        acum_dif = r["pf"] - r["pl"]
        mud = lote_dif - acum_dif
        tend = "≈ igual ao acumulado" if abs(mud) < 2 else (f"mais Flávio (+{mud:.0f} p.p.)" if mud > 0 else f"mais Lula ({mud:.0f} p.p.)")
        print(f"{r['uf']:<4}{r['ap0']:>6.0f}%→{r['ap1']:>4.0f}%{br(r['dv']):>15}"
              f"{r['pf_lote']:>8.1f} x {r['pl_lote']:<4.1f}{r['pf']:>8.1f} x {r['pl']:<4.1f}  {tend}")
    parados = [r["uf"] for r in linhas if r["dv"] <= 0 and r["ap1"] < 100]
    if parados:
        print(f"   sem votos novos: {', '.join(parados)}")

    print("\n2) O QUE AINDA FALTA E PARA ONDE PESA (se cada estado continuar votando como está)")
    print(f"{'UF':<4}{'apurado':>9}{'válidos que faltam':>20}{'placar F x L':>15}{'saldo esperado':>18}")
    tot_f = tot_l = 0
    for r in sorted(linhas, key=lambda r: -abs(r["saldo"])):
        if r["rest"] < 1:
            continue
        quem = "Flávio" if r["saldo"] > 0 else "Lula"
        tot_f += max(r["saldo"], 0)
        tot_l += max(-r["saldo"], 0)
        print(f"{r['uf']:<4}{r['ap1']:>8.0f}%{br(r['rest']):>20}{r['pf']:>8.1f} x {r['pl']:<4.1f}"
              f"{('+' + br(abs(r['saldo'])) + ' ' + quem):>20}")
    # diferença atual pela soma das UFs (o arquivo nacional do TSE atrasa)
    dif_atual = sum(ler(b, uf)["f"] - ler(b, uf)["l"] for uf in UFS)
    final = dif_atual + tot_f - tot_l
    print(f"\nDiferença atual: Flávio +{br(dif_atual)} votos")
    print(f"O que falta soma +{br(tot_f)} para o Flávio e +{br(tot_l)} para o Lula (saldo líquido {'+' if tot_f > tot_l else '−'}{br(abs(tot_f - tot_l))} {'Flávio' if tot_f > tot_l else 'Lula'})")
    print(f"Diferença projetada no fim: {'Flávio' if final > 0 else 'Lula'} +{br(abs(final))} votos")


def evolucao_uf(uf):
    print(f"Evolução de {uf} em todas as coletas\n")
    print(f"{'coleta':<7}{'apurado':>9}{'válidos':>13}{'acum F x L':>15}{'lote F x L':>15}{'faltam':>13}")
    ant = None
    for d in coletas():
        x = ler(d, uf)
        lote = ""
        if ant and x["vv"] > ant["vv"]:
            dv = x["vv"] - ant["vv"]
            lote = f"{(x['f'] - ant['f']) / dv * 100:.1f} x {(x['l'] - ant['l']) / dv * 100:.1f}"
        print(f"{hora(d):<7}{x['secoes']:>8.1f}%{br(x['vv']):>13}{x['f'] / x['vv'] * 100:>8.1f} x {x['l'] / x['vv'] * 100:<4.1f}"
              f"{lote:>15}{br(restante_validos(x)):>13}")
        ant = x


def main():
    args = sys.argv[1:]
    lista = coletas()
    if args and args[0] == "--todas":
        evolucao_uf(args[1].upper() if len(args) > 1 else "SP")
    elif len(args) == 2:
        comparar(achar(args[0], lista), achar(args[1], lista))
    else:
        comparar(lista[-2], lista[-1])


if __name__ == "__main__":
    main()
