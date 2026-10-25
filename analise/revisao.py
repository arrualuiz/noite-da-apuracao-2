#!/usr/bin/env python3
"""Confere as ideias da noite (os cases) contra a coleta mais recente.

Uso: python3 analise/revisao.py
Lê dados/apuracao.sqlite (atualizado a cada coleta).
"""
import sqlite3
from pathlib import Path

BANCO = Path(__file__).resolve().parent.parent / "dados" / "apuracao.sqlite"
con = sqlite3.connect(BANCO)


def q(sql, *a):
    return con.execute(sql, a).fetchall()


def estado(cid, uf=None):
    """Votos de Flávio/Lula, válidos e fração do eleitorado apurado (soma das UFs ou uma UF)."""
    w, args = ("abrangencia <> 'BR'", (cid,)) if uf is None else ("abrangencia = ?", (cid, uf))
    f = q(f"SELECT SUM(votos) FROM votos WHERE coleta_id=? AND {w} AND numero=22", *args)[0][0]
    l = q(f"SELECT SUM(votos) FROM votos WHERE coleta_id=? AND {w} AND numero=13", *args)[0][0]
    vv, el, ea, st, ts = q(f"""SELECT SUM(validos), SUM(eleitorado), SUM(eleitorado_apurado),
                               SUM(secoes_apuradas), SUM(secoes_total) FROM apuracao WHERE coleta_id=? AND {w}""", *args)[0]
    return {"f": f, "l": l, "vv": vv, "frac": ea / el, "secoes": st / ts * 100}


def projecao(cid):
    pf = pl = pv = 0.0
    for (uf,) in q("SELECT DISTINCT abrangencia FROM apuracao WHERE coleta_id=? AND abrangencia <> 'BR'", cid):
        x = estado(cid, uf)
        if x["frac"] > 0 and x["vv"]:
            pf += x["f"] / x["frac"]; pl += x["l"] / x["frac"]; pv += x["vv"] / x["frac"]
    return pf / pv * 100, pl / pv * 100


def precisa(x, k, alvo):
    """% dos válidos restantes de que o candidato precisa para terminar em `alvo`; None se nada mais falta."""
    final = x["vv"] / x["frac"]
    faltam = final - x["vv"]
    return None if faltam < 1 else (final * alvo / 100 - x[k]) / faltam * 100


def br(n):
    return f"{n:,.0f}".replace(",", ".")


col = [r[0] for r in q("SELECT coleta_id FROM coletas ORDER BY coleta_id")]
ult = col[-1]
c1818 = col[0]
c1914 = next(c for c in col if c >= "20261004-1914")
A = estado(ult)
pf_a, pl_a = A["f"] / A["vv"] * 100, A["l"] / A["vv"] * 100
proj_f, proj_l = projecao(ult)
p18_f, p18_l = projecao(c1818)
x18 = estado(c1818)

# lote mais recente
ant = estado(col[-2])
dv = A["vv"] - ant["vv"]
lote = ((A["f"] - ant["f"]) / dv * 100, (A["l"] - ant["l"]) / dv * 100) if dv > 0 else None

print(f"Coleta {ult[9:11]}:{ult[11:13]} · {A['secoes']:.2f}% das seções · Flávio {pf_a:.2f}% x Lula {pl_a:.2f}% · diferença {br(A['f'] - A['l'])}")
if lote:
    print(f"Último lote ({br(dv)} válidos): Flávio {lote[0]:.1f}% x Lula {lote[1]:.1f}%")
print(f"Projeção por estado agora: Flávio {proj_f:.2f}% x Lula {proj_l:.2f}%\n")


def linha(case, ideia, agora, veredito):
    print(f"{case:<4}{ideia:<42}{agora:<48}{veredito}")


print(f"{'':<4}{'ideia':<42}{'agora':<48}veredito")
linha("01", "placar parcial ≠ resultado (51,09% c/ 12%)", f"Flávio {pf_a:.2f}% (caiu {51.09 - pf_a:.2f} p.p.)", "✅")
e_proj, e_plac = abs(p18_f - pf_a), abs(x18["f"] / x18["vv"] * 100 - pf_a)
linha("03", "projeção 18:18 (49,0%) x placar 18:18", f"erro projeção {e_proj:.2f} x placar {e_plac:.2f} p.p.", "✅" if e_proj < e_plac else "❌")
linha("03b", "a projeção também desce?", f"18:18 {p18_f:.2f}% → agora {proj_f:.2f}%", "⚠️ sim" if proj_f < p18_f - .3 else "estável")
n50, n47, n42 = precisa(A, "f", 50), precisa(A, "f", 47), precisa(A, "l", 42)
if n50 is None:  # apuração encerrada: compara direto com o resultado
    linha("05", "Flávio precisa de 49,7% p/ 1º turno", f"terminou com {pf_a:.2f}%", "✅ 2º turno" if pf_a < 50 else "❌")
    linha("06", "palpite Flávio 47%", f"terminou com {pf_a:.2f}% (erro {47 - pf_a:+.2f})", "✅" if abs(47 - pf_a) < .5 else "❌")
    linha("06b", "palpite Lula 42%", f"terminou com {pl_a:.2f}% (erro {42 - pl_a:+.2f})", "✅" if abs(42 - pl_a) < .5 else "❌")
else:
    linha("05", "Flávio precisa de 49,7% p/ 1º turno", f"precisa de {n50:.1f}% do restante", "✅ inviável" if n50 > 55 else "🟡")
    linha("06", "palpite Flávio 47%", f"precisa de {n47:.1f}% do restante", "🟡 plausível" if lote and abs(lote[0] - n47) < 8 else "?")
    linha("06b", "palpite Lula 42%", f"já tem {pl_a:.2f}%; exigiria {n42:.1f}%", "❌" if n42 < 35 else "🟡")
x, y = estado(c1914, "SP"), estado(ult, "SP")
dsp = y["vv"] - x["vv"]
m_prev = (x["f"] - x["l"]) / x["vv"] * 100
m_real = ((y["f"] - x["f"]) - (y["l"] - x["l"])) / dsp * 100 if dsp else 0
linha("08", "SP cada vez menos favorável ao Flávio", f"margem prevista {m_prev:+.1f} x real {m_real:+.1f} (desde 19:14)", "✅" if m_real < m_prev else "❌")
if lote:
    linha("09", "lotes agora dão saldo a quem?", f"último lote: {'Flávio' if lote[0] > lote[1] else 'Lula'} +{abs(lote[0] - lote[1]):.1f} p.p.", "")

print("\nViés da projeção desde 19:14 (margem F−L prevista x real nos votos novos):")
tp = tr = 0
for uf in ["SP", "BA", "MG", "RJ", "CE", "PE", "MA", "PA"]:
    x, y = estado(c1914, uf), estado(ult, uf)
    d = y["vv"] - x["vv"]
    if d <= 0:
        continue
    sp = d * (x["f"] - x["l"]) / x["vv"]; sr = (y["f"] - x["f"]) - (y["l"] - x["l"])
    tp += sp; tr += sr
    print(f"  {uf}: previsto {sp:+12,.0f} · real {sr:+12,.0f}".replace(",", "."))
print(f"  total: previsto {br(tp)} · real {br(tr)} → projeção errou {br(abs(tr - tp))} a favor do {'Flávio' if tr < tp else 'Lula'}")
