#!/usr/bin/env python3
"""Analisa a evolução da apuração a partir de dados/snapshots.csv."""
import csv
from pathlib import Path

ARQUIVO = Path(__file__).resolve().parent.parent / "dados" / "snapshots.csv"
ESTADOS = Path(__file__).resolve().parent.parent / "dados" / "estados.csv"


def num(v):
    return float(v) if v not in ("", None) else None


def main():
    if not ARQUIVO.exists():
        print("Nenhum registro ainda. Use: python3 coleta/coletar.py")
        return
    with ARQUIVO.open(encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    if not linhas:
        print("Arquivo vazio.")
        return

    print(f"{'horário':<17} {'urnas':>6} {'Lula':>7} {'Flávio':>7} {'dif(F-L)':>9} {'Δdif':>7} {'Δdif/p.p. urna':>15}")
    print("-" * 75)
    ant = None
    for l in linhas:
        u, lu, fl = num(l["urnas_pct"]), num(l["lula_pct"]), num(l["flavio_pct"])
        dif = fl - lu
        delta = taxa = ""
        if ant:
            d = dif - ant[1]
            delta = f"{d:+.2f}"
            if u > ant[0]:
                taxa = f"{d / (u - ant[0]):+.3f}"
        print(f"{l['horario']:<17} {u:>5.1f}% {lu:>6.2f}% {fl:>6.2f}% {dif:>+8.2f} {delta:>7} {taxa:>15}")
        if l.get("nota"):
            print(f"{'':<17}   ↳ {l['nota']}")
        ant = (u, dif)

    ultimo = linhas[-1]
    u, lu, fl = num(ultimo["urnas_pct"]), num(ultimo["lula_pct"]), num(ultimo["flavio_pct"])
    dif = fl - lu
    print()

    # Quanto o Lula precisa nas urnas restantes para empatar
    # (aproximação: assume que urnas restantes têm o mesmo nº médio de votos)
    if u < 100:
        restante = 100 - u
        lula_atual_peso = lu * u
        flavio_atual_peso = fl * u
        # Lula precisa de x% dos votos dos 2 no restante: lula_atual + x*rest = flavio_atual + (1-x)*rest (normalizado nos dois)
        tot2 = lu + fl
        lu2, fl2 = lu / tot2, fl / tot2  # fatia entre os dois
        x = (fl2 * u - lu2 * u + restante) / (2 * restante)
        print(f"Faltam ~{restante:.1f}% das urnas.")
        print(f"Para empatar, o Lula precisaria de ~{x*100:.1f}% dos votos (entre os dois) nas urnas restantes.")
        print(f"  (hoje ele tem {lu2*100:.1f}% entre os dois)")

    # 1º turno: o líder fica acima de 50% dos válidos?
    if ultimo.get("flavio_votos") and ultimo.get("lula_votos") and u < 100:
        fv, lv = num(ultimo["flavio_votos"]), num(ultimo["lula_votos"])
        validos = (fv + lv) / ((lu + fl) / 100)
        validos_final = validos / (u / 100)  # aproximação: urnas ~ votos
        faltam = validos_final - validos
        precisa = (validos_final / 2 - fv) / faltam
        br = lambda n: f"{n:,.0f}".replace(",", ".")
        print(f"\n1º turno: ~{br(validos)} válidos contados, ~{br(validos_final)} esperados no total.")
        print(f"Para o Flávio fechar acima de 50% (sem 2º turno), ele precisa de {precisa*100:.1f}% dos válidos restantes.")
        print(f"  (até agora ele tem {fl:.2f}%)")

    # Projeção linear da diferença até 100% (ingênua!)
    if len(linhas) >= 2:
        pts = [(num(l["urnas_pct"]), num(l["flavio_pct"]) - num(l["lula_pct"])) for l in linhas]
        n = len(pts)
        mx = sum(p[0] for p in pts) / n
        my = sum(p[1] for p in pts) / n
        sxx = sum((p[0] - mx) ** 2 for p in pts)
        if sxx > 0:
            b = sum((p[0] - mx) * (p[1] - my) for p in pts) / sxx
            a = my - b * mx
            proj = a + b * 100
            quem = "Flávio" if proj > 0 else "Lula"
            print(f"\nTendência linear: diferença muda {b:+.3f} p.p. a cada 1% de urnas.")
            print(f"Projeção ingênua em 100%: {quem} +{abs(proj):.2f} p.p.")
            if b != 0:
                virada = -a / b
                if u < virada <= 100:
                    print(f"Se a tendência continuar, a liderança vira por volta de {virada:.0f}% das urnas.")
            print("⚠ Projeção linear ignora a ordem regional de chegada das urnas — use com cautela.")

    analisar_estados()


def analisar_estados():
    if not ESTADOS.exists():
        return
    with ESTADOS.open(encoding="utf-8") as f:
        ultimos = {}
        for l in csv.DictReader(f):
            ultimos[l["uf"]] = l  # fica a leitura mais recente de cada UF
    linhas = []
    for uf, l in ultimos.items():
        u, el = num(l["urnas_pct"]), num(l["eleitorado"])
        linhas.append((el * (100 - u) / 100, uf, u, el, l))
    linhas.sort(reverse=True)
    total_rest = sum(x[0] for x in linhas)
    print(f"\n=== Onde ainda faltam votos (estados registrados) ===")
    print(f"{'UF':<4} {'apurado':>8} {'eleitorado':>12} {'ainda falta':>12} {'% do que falta':>15}  Flávio x Lula")
    for rest, uf, u, el, l in linhas:
        placar = ""
        if l["flavio_pct"] and l["lula_pct"]:
            placar = f"{num(l['flavio_pct']):.1f} x {num(l['lula_pct']):.1f}"
        print(f"{uf:<4} {u:>7.1f}% {el:>12,.0f} {rest:>12,.0f} {rest/total_rest*100:>14.1f}%  {placar}".replace(",", "."))

    # Projeção ponderada: cada estado termina com o placar atual dele,
    # pesado pelo eleitorado. Corrige o viés de "quem foi apurado primeiro".
    com_placar = [x for x in linhas if x[4]["flavio_pct"] and x[4]["lula_pct"] and x[2] > 0]
    if com_placar:
        peso = sum(x[3] for x in com_placar)
        pf = sum(x[3] * num(x[4]["flavio_pct"]) for x in com_placar) / peso
        pl = sum(x[3] * num(x[4]["lula_pct"]) for x in com_placar) / peso
        cobertura = peso / sum(x[3] for x in linhas) * 100
        print(f"\nProjeção por estado (cada UF termina como está agora, peso = eleitorado):")
        print(f"  Flávio {pf:.2f}% x Lula {pl:.2f}%  — cobre {cobertura:.0f}% do eleitorado registrado")
        print(f"  {'Flávio venceria no 1º turno' if pf > 50 else '→ indica 2º turno'} (assume comparecimento e % de válidos iguais entre estados)")


if __name__ == "__main__":
    main()
