#!/usr/bin/env python3
"""Mínimos e máximos de cada coisa que medi, e quem é cada registro (cidade ou estado).

Para cada parâmetro, mostra o menor e o maior valor, com o nome da cidade, o % e o número de pessoas.
Nos parâmetros em %, cidades muito pequenas dominam os extremos (poucos votos mexem muito no %),
então eles saem duas vezes: entre todas as cidades e só entre as de 50 mil eleitores ou mais.
Nas diferenças entre Lula e Flávio, mostra também o mais perto de zero (o quase empate).
Só entram cidades 100% apuradas no 2º turno. O exterior (ZZ) fica de fora das cidades.

Usa os arquivos de todos os municípios baixados por analise/abstencao.py.
Gera dados/extremos.csv.

Uso: python3 analise/abstencao.py && python3 analise/extremos.py
"""
import csv
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "dados"
PASTA_1T = PASTA / "historico" / "tse" / "1t-municipios"
SAIDA = PASTA / "extremos.csv"
NUM_1T = {"13": "lula", "22": "flavio", "70": "cury", "14": "renan", "55": "caiado"}
GRANDE = 50_000


def mil(n):
    return f"{n:,.0f}".replace(",", ".")


def ler(arq, segundo_turno):
    u = json.loads(arq.read_text(encoding="utf-8"))
    e, v = u["e"], u["v"]
    c = {x["n"]: int(x["vap"]) for a in u["carg"][0]["agr"] for p in a["par"] for x in p["cand"]}
    out = {"te": int(e["te"]), "est": int(e["est"]), "c": int(e["c"]), "a": int(e["a"]),
           "vv": int(v["vv"]), "vb": int(v["vb"]), "vn": int(v["tvn"]), "lula": c.get("13", 0), "flavio": c.get("22", 0)}
    if not segundo_turno:
        for n, k in NUM_1T.items():
            out[k] = c.get(n, 0)
        out["outros"] = out["vv"] - out["lula"] - out["flavio"]
    return out


def medidas(x, y):
    """x = 2º turno, y = 1º turno. Devolve {parâmetro: (valor, pessoas ou None)}."""
    pct = lambda a, b: a / b * 100 if b else None
    lf, lf1 = x["lula"] + x["flavio"], y["lula"] + y["flavio"]
    pl, pl1 = pct(x["lula"], lf), pct(y["lula"], lf1)
    bn, bn1 = x["vb"] + x["vn"], y["vb"] + y["vn"]
    return {
        "Eleitorado": (x["te"], x["te"]),
        "Comparecimento (%)": (pct(x["c"], x["c"] + x["a"]), x["c"]),
        "Abstenção (%)": (pct(x["a"], x["c"] + x["a"]), x["a"]),
        "Abstenção: variação do 1º para o 2º turno (pts)": (pct(x["a"], x["c"] + x["a"]) - pct(y["a"], y["c"] + y["a"]), x["a"] - y["a"]),
        "Brancos (% de quem foi votar)": (pct(x["vb"], x["c"]), x["vb"]),
        "Nulos (% de quem foi votar)": (pct(x["vn"], x["c"]), x["vn"]),
        "Brancos + nulos: variação do 1º para o 2º turno (pts)": (pct(bn, x["c"]) - pct(bn1, y["c"]), bn - bn1),
        "Lula (% dos válidos)": (pl, x["lula"]),
        "Flávio (% dos válidos)": (100 - pl, x["flavio"]),
        "Diferença Lula - Flávio (pts)": (pl - (100 - pl), x["lula"] - x["flavio"]),
        "Lula: votos ganhos do 1º para o 2º turno (% sobre o 1º)": (pct(x["lula"] - y["lula"], y["lula"]), x["lula"] - y["lula"]),
        "Flávio: votos ganhos do 1º para o 2º turno (% sobre o 1º)": (pct(x["flavio"] - y["flavio"], y["flavio"]), x["flavio"] - y["flavio"]),
        "Mudança do Lula entre Lula e Flávio, 1º → 2º turno (pts)": (pl - pl1, None),
        "Cury no 1º turno (% dos válidos)": (pct(y["cury"], y["vv"]), y["cury"]),
        "Renan no 1º turno (% dos válidos)": (pct(y["renan"], y["vv"]), y["renan"]),
        "Caiado no 1º turno (% dos válidos)": (pct(y["caiado"], y["vv"]), y["caiado"]),
        "Outros candidatos no 1º turno, somados (% dos válidos)": (pct(y["outros"], y["vv"]), y["outros"]),
    }


PERTO_DE_ZERO = {"Diferença Lula - Flávio (pts)", "Mudança do Lula entre Lula e Flávio, 1º → 2º turno (pts)",
                 "Abstenção: variação do 1º para o 2º turno (pts)"}
SO_PESSOAS = {"Eleitorado"}


def carregar():
    pasta_2t = max((d / "todos-mun" for d in (PASTA / "brutos").iterdir() if (d / "todos-mun").exists()),
                   key=lambda p: p.parent.name)
    cfg = json.loads((PASTA / "municipios-6258.json").read_text(encoding="utf-8"))
    cidades, ufs = [], {}
    for a in cfg["abr"]:
        uf = a["cd"].upper()
        for m in a["mu"]:
            f2, f1 = pasta_2t / f"{a['cd']}{m['cd']}.json", PASTA_1T / f"{a['cd']}{m['cd']}.json"
            if not (f2.exists() and f1.exists()):
                continue
            x, y = ler(f2, True), ler(f1, False)
            if uf != "ZZ":  # estados: soma de todas as cidades, apuradas ou não
                for k, d in (("x", x), ("y", y)):
                    s = ufs.setdefault(uf, {"x": {}, "y": {}})[k]
                    for c, v in d.items():
                        s[c] = s.get(c, 0) + v
            if uf == "ZZ" or x["est"] < x["te"] or not (x["lula"] + x["flavio"]) or not (y["lula"] + y["flavio"]):
                continue
            cidades.append({"nome": f"{m['nm'].title()} ({uf})", "te": x["te"], "m": medidas(x, y)})
    estados = [{"nome": uf, "te": s["x"]["te"], "m": medidas(s["x"], s["y"])} for uf, s in sorted(ufs.items())]
    return pasta_2t, cidades, estados


def fmt(par, r):
    v, p = r["m"][par]
    if par in SO_PESSOAS:
        txt = f"{mil(v)} eleitores"
    else:
        txt = f"{v:+.2f} pts" if "(pts)" in par else f"{v:.2f}%"
        if p is not None:
            txt += f" · {'+' if p > 0 and ('variação' in par or 'ganhos' in par or 'Diferença' in par) else ''}{mil(p)} pessoas"
    return f"{r['nome']} — {txt} ({mil(r['te'])} eleitores)" if par not in SO_PESSOAS else f"{r['nome']} — {txt}"


def extremos(registros, par):
    ok = [r for r in registros if r["m"][par][0] is not None]
    ok.sort(key=lambda r: r["m"][par][0])
    out = [("mínimo", ok[0]), ("máximo", ok[-1])]
    if par in PERTO_DE_ZERO:
        out.append(("mais perto de zero", min(ok, key=lambda r: abs(r["m"][par][0]))))
    # empates no extremo (ex.: várias cidades com 0 brancos)
    return [(tipo, r, sum(1 for o in ok if o["m"][par][0] == r["m"][par][0]) - 1) for tipo, r in out]


def main():
    pasta_2t, cidades, estados = carregar()
    grandes = [c for c in cidades if c["te"] >= GRANDE]
    hora = pasta_2t.parent.name
    print(f"MÍNIMOS E MÁXIMOS · {len(cidades)} cidades 100% apuradas às {hora[9:11]}:{hora[11:13]}"
          f" ({len(grandes)} com {mil(GRANDE)} eleitores ou mais) e os 27 estados\n")
    linhas = []
    for par in cidades[0]["m"]:
        print(f"■ {par}")
        grupos = [("cidades", cidades)]
        if par not in SO_PESSOAS:
            grupos.append((f"cidades com {mil(GRANDE)}+ eleitores", grandes))
        grupos.append(("estados", estados))
        for grupo, regs in grupos:
            for tipo, r, emp in extremos(regs, par):
                extra = f"  (empatada com mais {emp})" if emp else ""
                print(f"   {grupo:28} {tipo:19} {fmt(par, r)}{extra}")
                v, p = r["m"][par]
                linhas.append({"parametro": par, "grupo": grupo, "tipo": tipo, "registro": r["nome"],
                               "valor": round(v, 4), "pessoas": p, "eleitorado": r["te"], "empatados": emp})
        print()
    with SAIDA.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    print(f"Gravado em {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
