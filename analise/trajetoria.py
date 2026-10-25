#!/usr/bin/env python3
"""O caminho provável do placar até 100%: o Lula ainda sobe, ou sobe e depois cai?

Para cada estado (e SP dividido em capital, Grande SP e interior), usa:
  - quanto falta apurar (eleitores) e a velocidade de apuração dos últimos ~10 min;
  - o % do Lula esperado no que falta, tirado da previsão (analise/perguntas.py).
Depois avança minuto a minuto, cada lugar no seu ritmo, e mostra o placar nacional no caminho.

Uso: python3 analise/trajetoria.py   (o analise/perguntas.py também chama simular() a cada coleta,
                                      guarda o caminho em dados/trajetorias.csv e desenha no painel)
"""
import csv
import json
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "dados"
JANELA_MIN = 10


def coletas():
    return sorted(d for d in (PASTA / "brutos").iterdir() if (d / "br-u.json").exists())


def hora(pasta):
    return datetime.strptime(pasta.name, "%Y%m%d-%H%M%S")


def uf_json(pasta, uf):
    u = json.loads((pasta / f"{uf.lower()}-u.json").read_text(encoding="utf-8"))
    c = {x["n"]: int(x["vap"]) for a in u["carg"][0]["agr"] for p in a["par"] for x in p["cand"]}
    return {"l": c.get("13", 0), "f": c.get("22", 0), "te": int(u["e"]["te"]), "est": int(u["e"]["est"])}


def segmentos_sp(coleta_id):
    """Capital, Grande SP e interior de SP numa coleta (de dados/segmentos.csv)."""
    out = {}
    for r in csv.DictReader((PASTA / "segmentos.csv").open(encoding="utf-8")):
        if r["coleta_id"] == coleta_id and r["segmento"].startswith(("SP ", "Grande SP")):
            out[r["segmento"]] = {"l": int(r["lula"]), "f": int(r["flavio"]),
                                  "te": int(r["eleitorado"]), "est": int(r["apurado_eleit"])}
    return out


def simular():
    """Simula o resto da apuração. Devolve o ponto de partida, o caminho e o resumo por lugar."""
    lista = coletas()
    agora = lista[-1]
    antes = min(lista, key=lambda p: abs((hora(agora) - hora(p)).total_seconds() / 60 - JANELA_MIN))
    minutos = (hora(agora) - hora(antes)).total_seconds() / 60
    prev = {r["uf"]: r for r in csv.DictReader((PASTA / "perguntas_uf.csv").open(encoding="utf-8"))}

    # cada lugar: votos de Lula e Flávio que faltam (previsão) e quanto do eleitorado é apurado por minuto
    lugares = {}
    for uf, r in prev.items():
        x, x0 = uf_json(agora, uf), uf_json(antes, uf)
        falta_l, falta_f = int(r["prev_lula"]) - x["l"], int(r["prev_flavio"]) - x["f"]
        lugares[uf] = {"l": x["l"], "f": x["f"], "falta_l": max(falta_l, 0), "falta_f": max(falta_f, 0),
                       "falta_el": x["te"] - x["est"], "ritmo": max(x["est"] - x0["est"], 0) / minutos}

    # SP em três partes: o que falta no estado é dividido pelo eleitorado que falta em cada parte,
    # com o % do Lula de cada parte deslocado para fechar com a previsão do estado
    seg, seg0 = segmentos_sp(agora.name), segmentos_sp(antes.name)
    if len(seg) == 3 and len(seg0) == 3:
        sp = lugares.pop("SP")
        falta_v = sp["falta_l"] + sp["falta_f"]
        pesos = {k: s["te"] - s["est"] for k, s in seg.items()}
        tot = sum(pesos.values())
        obs = {k: s["l"] / (s["l"] + s["f"]) for k, s in seg.items()}
        alvo = sp["falta_l"] / falta_v
        delta = alvo - sum(obs[k] * pesos[k] / tot for k in seg)
        for k, s in seg.items():
            v = falta_v * pesos[k] / tot
            share = min(max(obs[k] + delta, 0), 1)
            lugares[k] = {"l": s["l"], "f": s["f"], "falta_l": v * share, "falta_f": v * (1 - share),
                          "falta_el": pesos[k], "ritmo": max(s["est"] - seg0[k]["est"], 0) / minutos}

    # avança minuto a minuto; lugar parado (ritmo 0) entra no fim, no ritmo médio
    ritmo_medio = sum(p["ritmo"] for p in lugares.values()) / len(lugares)
    for p in lugares.values():
        if p["ritmo"] <= 0:
            p["ritmo"] = ritmo_medio
    resumo = [(p["falta_el"] / p["ritmo"], nome, p["falta_el"],
               p["falta_l"] / (p["falta_l"] + p["falta_f"]) * 100 if p["falta_l"] + p["falta_f"] else 0)
              for nome, p in lugares.items()]
    total_el = sum(p["falta_el"] for p in lugares.values())
    caminho, t = [], 0
    while any(p["falta_el"] > 1 for p in lugares.values()) and t < 600:
        for p in lugares.values():
            if p["falta_el"] <= 1:
                continue
            frac = min(p["ritmo"] / p["falta_el"], 1)
            for k in ("l", "f"):
                v = p[f"falta_{k}"] * frac
                p[k] += v
                p[f"falta_{k}"] -= v
            p["falta_el"] -= p["falta_el"] * frac
        t += 1
        L, F = sum(p["l"] for p in lugares.values()), sum(p["f"] for p in lugares.values())
        resta = sum(p["falta_el"] for p in lugares.values())
        caminho.append((t, 1 - resta / total_el, L / (L + F) * 100))

    pct_agora = float(json.loads((agora / "br-u.json").read_text(encoding="utf-8"))["s"]["pstn"].replace(",", "."))
    x = {uf: uf_json(agora, uf) for uf in prev}
    L0, F0 = sum(v["l"] for v in x.values()), sum(v["f"] for v in x.values())
    # no gráfico, o caminho vai do % de seções de agora até 100%, na proporção do eleitorado que falta
    caminho = [(m, round(pct_agora + frac * (100 - pct_agora), 2), round(l, 3)) for m, frac, l in caminho]
    return {"agora": agora, "antes": antes, "secoes": pct_agora, "lula": L0 / (L0 + F0) * 100,
            "caminho": caminho, "resumo": resumo}


def guardar(s):
    """Acrescenta o caminho desta coleta em dados/trajetorias.csv (um ponto a cada 5 min e o final)."""
    arq = PASTA / "trajetorias.csv"
    if arq.exists() and s["agora"].name in arq.read_text(encoding="utf-8"):
        return
    novo = not arq.exists()
    pontos = [c for c in s["caminho"] if c[0] % 5 == 0]
    if s["caminho"][-1][0] % 5:
        pontos.append(s["caminho"][-1])
    with arq.open("a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if novo:
            w.writerow(["coleta_id", "minutos", "secoes_pct", "pct_lula"])
        w.writerows([s["agora"].name, *c] for c in pontos)


def main():
    s = simular()
    agora, antes, pct_agora, caminho, resumo = s["agora"], s["antes"], s["secoes"], s["caminho"], s["resumo"]
    print(f"Agora ({agora.name[9:11]}:{agora.name[11:13]}, {pct_agora:.1f}% das seções): Lula {s['lula']:.2f}%")
    print(f"Ritmo medido entre {antes.name[9:11]}:{antes.name[11:13]} e {agora.name[9:11]}:{agora.name[11:13]}\n")
    print("Caminho provável do placar (Lula):")
    marcos = [m for m in (10, 20, 30, 45, 60, 90, 120, 180, 240) if m <= len(caminho)]
    for m in marcos:
        tt, sec, l = caminho[m - 1]
        print(f"  +{tt:3d} min · ~{sec:5.1f}% das seções · Lula {l:.2f}%")
    tt, sec, l = caminho[-1]
    print(f"  fim (+{tt} min) · Lula {l:.2f}%")
    pico = max(caminho, key=lambda c: c[2])
    print(f"\nPico: Lula {pico[2]:.2f}% daqui a ~{pico[0]} min · final {caminho[-1][2]:.2f}%")

    print("\nO que falta, em ordem de quando deve terminar (lugares com 50 mil eleitores ou mais faltando):")
    for mins, nome, falta, lula in sorted(resumo):
        if falta >= 50_000:
            print(f"  {nome:27} faltam {falta / 1e6:5.2f} mi eleitores · termina em ~{mins:4.0f} min · Lula no que falta ~{lula:.0f}%")


if __name__ == "__main__":
    main()
