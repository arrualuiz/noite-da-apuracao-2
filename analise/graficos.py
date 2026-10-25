#!/usr/bin/env python3
"""Gera os gráficos (SVG) dos cases em cases/graficos/, a partir do banco e dos CSVs.

Uso: python3 analise/graficos.py
Cada case referencia o seu gráfico em Markdown: ![descrição](graficos/NN-nome.svg)
Cores legíveis em fundo claro e escuro, nas cores dos partidos: azul = PL (Flávio), vermelho = PT (Lula).
"""
import csv
import json
import sqlite3
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"
SAIDA = RAIZ / "cases" / "graficos"

AZUL, VERMELHO, CINZA, LARANJA = "#2a78d6", "#e34948", "#9a998f", "#c8692e"
TEXTO, GRADE = "#7d7c75", "#cfcdc6"
FONTE = "font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif"


def br(v, d=1):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class SVG:
    def __init__(self, w, h, titulo):
        self.w, self.h, self.p = w, h, []
        self.p.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
                      f'role="img" aria-label="{esc(titulo)}" style="{FONTE}">')
        self.p.append(f"<title>{esc(titulo)}</title>")

    def t(self, x, y, s, size=12, cor=TEXTO, anchor="start", peso=400):
        self.p.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{cor}" text-anchor="{anchor}" '
                      f'font-weight="{peso}">{esc(s)}</text>')

    def l(self, x1, y1, x2, y2, cor=GRADE, w=1, dash=None, op=1):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.p.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{cor}" '
                      f'stroke-width="{w}" opacity="{op}"{d}/>')

    def r(self, x, y, w, h, cor, rx=3):
        if w < 0:
            x, w = x + w, -w
        if h < 0:
            y, h = y + h, -h
        self.p.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, .5):.1f}" height="{max(h, .5):.1f}" fill="{cor}" rx="{rx}"/>')

    def poly(self, pts, cor, w=2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        pp = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.p.append(f'<polyline points="{pp}" fill="none" stroke="{cor}" stroke-width="{w}" '
                      f'stroke-linejoin="round" stroke-linecap="round"{d}/>')

    def c(self, x, y, cor, r=4, op=1):
        o = f' fill-opacity="{op}"' if op != 1 else ""
        self.p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{round(r, 1):g}" fill="{cor}"{o}/>')

    def salvar(self, nome):
        self.p.append("</svg>")
        SAIDA.mkdir(parents=True, exist_ok=True)
        (SAIDA / nome).write_text("\n".join(self.p), encoding="utf-8")
        return nome


def legenda(s, x, y, itens):
    for nome, cor, dash in itens:
        s.l(x, y - 4, x + 20, y - 4, cor, 2.5, dash)
        s.t(x + 26, y, nome)
        x += 34 + len(nome) * 6.6


def linhas(nome, titulo, series, xlab, ylab, xdom, ydom, refs=(), w=720, h=380, fmt_x=lambda v: f"{v:g}",
           fmt_y=lambda v: f"{v:g}", ticks_y=None, ticks_x=None, rotulos_fim=True, fmt_fim=lambda v: br(v, 1)):
    """series: [(nome, cor, [(x, y)], dash)]; refs: [(y, rótulo)]"""
    s = SVG(w, h, titulo)
    m = dict(t=46, r=110, b=44, l=52)
    X = lambda v: m["l"] + (v - xdom[0]) / (xdom[1] - xdom[0]) * (w - m["l"] - m["r"])
    Y = lambda v: h - m["b"] - (v - ydom[0]) / (ydom[1] - ydom[0]) * (h - m["t"] - m["b"])
    legenda(s, m["l"], 18, [(n, c, d) for n, c, _, d in series])
    for v in ticks_y or []:
        s.l(m["l"], Y(v), w - m["r"], Y(v))
        s.t(m["l"] - 8, Y(v) + 4, fmt_y(v), 11, anchor="end")
    for v in ticks_x or []:
        s.t(X(v), h - m["b"] + 18, fmt_x(v), 11, anchor="middle")
    s.l(m["l"], h - m["b"], w - m["r"], h - m["b"], TEXTO, 1, op=.5)
    for v, rot in refs:
        s.l(m["l"], Y(v), w - m["r"], Y(v), TEXTO, 1.2, "5 4")
        s.t(w - m["r"] + 6, Y(v) + 4, rot, 11)
    fins = []
    for n, cor, pts, dash in series:
        pts = [(x, y) for x, y in pts if xdom[0] <= x <= xdom[1]]
        if not pts:
            continue
        s.poly([(X(x), Y(y)) for x, y in pts], cor, 2.4, dash)
        if rotulos_fim and not dash:
            x, y = pts[-1]
            s.c(X(x), Y(y), cor)
            fins.append([Y(y) + 4, X(x) + 8, fmt_fim(y), cor])
    fins.sort()
    for i in range(1, len(fins)):  # afasta rótulos que se encostam
        fins[i][0] = max(fins[i][0], fins[i - 1][0] + 14)
    for yy, xx, txt, cor in fins:
        s.t(xx, yy, txt, 12, cor, peso=700)
    s.t((m["l"] + w - m["r"]) / 2, h - 8, xlab, 11, anchor="middle")
    s.t(12, m["t"] - 14, ylab, 11)
    return s.salvar(nome)


def barras_h(nome, titulo, itens, fmt=lambda v: br(v), ref=None, w=720, rotulo_x="", altura_barra=22, notas=None, vmin=None):
    """itens: [(rótulo, valor, cor)] — barras horizontais; valores negativos vão para a esquerda do zero."""
    n = len(itens)
    m = dict(t=30 if not notas else 50, r=90, b=34, l=170)
    h = m["t"] + m["b"] + n * (altura_barra + 8)
    s = SVG(w, h, titulo)
    if notas:
        legenda(s, m["l"], 18, notas)
    base = 0 if vmin is None else vmin
    vmax = max(0, max(v for _, v, _ in itens))
    vmin = min(base, min(v for _, v, _ in itens)) if vmin is None else vmin
    if ref is not None:
        vmax = max(vmax, ref); vmin = min(vmin, ref)
    faixa = vmax - vmin
    if vmin < 0:
        vmin -= faixa * .22   # espaço para o rótulo das barras negativas
    vmax += faixa * .14       # espaço para o rótulo das positivas
    X = lambda v: m["l"] + (v - vmin) / ((vmax - vmin) or 1) * (w - m["l"] - m["r"])
    for i, (rot, v, cor) in enumerate(itens):
        y = m["t"] + i * (altura_barra + 8)
        s.t(m["l"] - 8, y + altura_barra / 2 + 4, rot, 12, anchor="end")
        s.r(X(base), y, X(v) - X(base), altura_barra, cor)
        s.t(X(v) + (6 if v >= base else -6), y + altura_barra / 2 + 4, fmt(v), 11, TEXTO, "start" if v >= base else "end", 600)
    s.l(X(base), m["t"] - 6, X(base), h - m["b"] + 4, TEXTO, 1, op=.6)
    if base:
        s.t(X(base), h - m["b"] + 18, fmt(base), 11, anchor="middle")
    if ref is not None:
        s.l(X(ref), m["t"] - 6, X(ref), h - m["b"] + 4, LARANJA, 1.5, "5 4")
        s.t(X(ref), h - m["b"] + 18, f"{fmt(ref)}", 11, LARANJA, "middle", 700)
    if rotulo_x:
        s.t((m["l"] + w - m["r"]) / 2, h - 6, rotulo_x, 11, anchor="middle")
    return s.salvar(nome)


def barras_agrupadas(nome, titulo, categorias, series, fmt=lambda v: br(v), w=720, h=340, ref=None, ref_rot=""):
    """categorias: [rótulo]; series: [(nome, cor, [valores])] — barras verticais lado a lado."""
    s = SVG(w, h, titulo)
    m = dict(t=46, r=30, b=56, l=52)
    vals = [v for _, _, vs in series for v in vs] + ([ref] if ref is not None else [])
    vmin, vmax = min(0, min(vals)), max(vals) * 1.12
    Y = lambda v: h - m["b"] - (v - vmin) / (vmax - vmin) * (h - m["t"] - m["b"])
    largura = (w - m["l"] - m["r"]) / len(categorias)
    bw = min(34, (largura * .7) / len(series))
    legenda(s, m["l"], 18, [(n, c, None) for n, c, _ in series])
    for i, cat in enumerate(categorias):
        x0 = m["l"] + i * largura + (largura - bw * len(series) - 2 * (len(series) - 1)) / 2
        for j, (_, cor, vs) in enumerate(series):
            x = x0 + j * (bw + 2)
            s.r(x, Y(max(vs[i], 0)), bw, abs(Y(vs[i]) - Y(0)), cor)
            s.t(x + bw / 2, Y(vs[i]) - 5 if vs[i] >= 0 else Y(vs[i]) + 13, fmt(vs[i]), 10, TEXTO, "middle", 600)
        for k, parte in enumerate(str(cat).split("\n")):
            s.t(m["l"] + i * largura + largura / 2, h - m["b"] + 16 + k * 13, parte, 11, anchor="middle")
    s.l(m["l"], Y(0), w - m["r"], Y(0), TEXTO, 1, op=.6)
    if ref is not None:
        s.l(m["l"], Y(ref), w - m["r"], Y(ref), LARANJA, 1.5, "5 4")
        s.t(w - m["r"], Y(ref) - 6, ref_rot, 11, LARANJA, "end", 700)
    return s.salvar(nome)


def dispersao(nome, titulo, pontos, xlab, ylab, xdom, ydom, ticks_x, ticks_y, fmt_x=lambda v: f"{v:g}",
              fmt_y=lambda v: f"{v:g}", refs=(), rotulos=(), notas=None, w=720, h=420):
    """pontos: [(x, y, raio, cor)]; refs: [(y, rótulo)] linhas horizontais; rotulos: [(x, y, texto, dx, dy)]."""
    s = SVG(w, h, titulo)
    m = dict(t=46 if notas else 24, r=24, b=44, l=52)
    X = lambda v: m["l"] + (v - xdom[0]) / (xdom[1] - xdom[0]) * (w - m["l"] - m["r"])
    Y = lambda v: h - m["b"] - (v - ydom[0]) / (ydom[1] - ydom[0]) * (h - m["t"] - m["b"])
    if notas:
        x = m["l"]
        for rot, cor in notas:
            s.c(x + 5, 14, cor, 5, .7); s.t(x + 15, 18, rot); x += 30 + len(rot) * 6.6
    for v in ticks_y:
        s.l(m["l"], Y(v), w - m["r"], Y(v), TEXTO if v == 0 else GRADE, 1, op=.6 if v == 0 else 1)
        s.t(m["l"] - 8, Y(v) + 4, fmt_y(v), 11, anchor="end")
    for v in ticks_x:
        s.t(X(v), h - m["b"] + 18, fmt_x(v), 11, anchor="middle")
    for y, rot in refs:
        s.l(m["l"], Y(y), w - m["r"], Y(y), LARANJA, 1.5, "5 4")
        s.t(w - m["r"], Y(y) - 6, rot, 11, LARANJA, "end", 700)
    for x, y, r, cor in sorted(pontos, key=lambda p: -p[2]):   # os maiores embaixo
        s.c(X(x), Y(y), cor, r, .55)
    for x, y, txt, dx, dy in rotulos:
        s.t(X(x) + dx, Y(y) + dy, txt, 11, TEXTO, "start" if dx >= 0 else "end", 700)
    s.t((m["l"] + w - m["r"]) / 2, h - 8, xlab, 11, anchor="middle")
    s.t(12, m["t"] - 10, ylab, 11)
    return s.salvar(nome)


# ---------------------------------------------------------------- dados
def con():
    return sqlite3.connect(DADOS / "apuracao.sqlite")


def nacional():
    return list(csv.DictReader(open(DADOS / "export" / "nacional.csv", encoding="utf-8-sig")))


def estado(c, cid, uf=None):
    q = lambda sql, *a: c.execute(sql, a).fetchall()
    w, a = ("abrangencia <> 'BR'", (cid,)) if uf is None else ("abrangencia = ?", (cid, uf))
    f = q(f"SELECT COALESCE(SUM(votos),0) FROM votos WHERE coleta_id=? AND {w} AND numero=22", *a)[0][0]
    l = q(f"SELECT COALESCE(SUM(votos),0) FROM votos WHERE coleta_id=? AND {w} AND numero=13", *a)[0][0]
    vv, el, ea, st, ts = q(f"""SELECT SUM(validos), SUM(eleitorado), SUM(eleitorado_apurado), SUM(secoes_apuradas),
                               SUM(secoes_total) FROM apuracao WHERE coleta_id=? AND {w}""", *a)[0]
    return dict(f=f, l=l, vv=vv, frac=ea / el, sec=st / ts * 100)


def coletas(c):
    return [r[0] for r in c.execute("SELECT coleta_id FROM coletas ORDER BY coleta_id")]


def hhmm(cid):
    return f"{cid[9:11]}:{cid[11:13]}"


def uol22():
    d = json.load(open(DADOS / "uol-historico-2022.json"))
    t = d["tuple"]; il, ib = t.index("candidate13Percent"), t.index("candidate22Percent")
    return [(p[0], p[ib], p[il]) for p in d["series"]]


# ---------------------------------------------------------------- gráficos
def g01(c):
    cid = coletas(c)[0]
    ufs = [r[0] for r in c.execute("SELECT DISTINCT abrangencia FROM apuracao WHERE coleta_id=? AND abrangencia<>'BR'", (cid,))]
    reg = dict(c.execute("SELECT uf, regiao FROM ufs").fetchall())
    cor = {"Sul": AZUL, "Sudeste": "#6da7ec", "Centro-Oeste": "#86b6ef", "Norte": "#ec835a", "Nordeste": VERMELHO, "Exterior": CINZA}
    itens = sorted(((f"{uf} ({reg[uf]})", estado(c, cid, uf)["sec"], cor[reg[uf]]) for uf in ufs), key=lambda x: -x[1])
    return barras_h("01-apurado-por-estado-1818.svg", "Seções apuradas por estado às 18:18", itens,
                    fmt=lambda v: br(v) + "%", rotulo_x="% das seções apuradas às 18:18 (cor = região)", altura_barra=14)


def g03(c):
    n = nacional()
    pts = lambda k: [(float(r["secoes_pct"]), float(r[k])) for r in n]
    return linhas("03-placar-x-projecao.svg", "Placar x projeção por estado ao longo da noite",
                  [("Flávio: placar", AZUL, pts("pct_flavio"), None), ("Flávio: projeção", AZUL, pts("proj_flavio"), "6 4"),
                   ("Lula: placar", VERMELHO, pts("pct_lula"), None), ("Lula: projeção", VERMELHO, pts("proj_lula"), "6 4")],
                  "% das seções apuradas", "% dos votos válidos", (15, 100), (40, 53), refs=[(50, "50%")],
                  ticks_y=range(40, 54, 2), ticks_x=range(20, 101, 10), fmt_x=lambda v: f"{v}%", fmt_y=lambda v: f"{br(v)}%" if v % 1 else f"{v:g}%", fmt_fim=lambda v: br(v, 1) + "%")


def g04(c):
    pts_u, pts_ab = [], []
    for i, cid in enumerate(coletas(c)[:10]):
        pasta = DADOS / "brutos" / cid
        u = json.load(open(pasta / "br-u.json", encoding="utf-8"))
        ab = next(a for a in json.load(open(pasta / "br-ab.json", encoding="utf-8"))["abr"] if a["cdabr"] == "br")
        pts_u.append((i, float(u["s"]["pstn"].replace(",", "."))))
        pts_ab.append((i, float(ab["s"]["pstn"].replace(",", "."))))
    cids = coletas(c)[:10]
    return linhas("04-dois-arquivos-do-tse.svg", "% de seções apuradas segundo cada arquivo do TSE",
                  [("arquivo de votos (-u.json): o certo", AZUL, pts_u, None), ("arquivo de andamento (-ab.json): adiantado", LARANJA, pts_ab, None)],
                  "coleta", "% das seções apuradas", (0, len(cids) - 1), (15, 85), ticks_y=range(20, 81, 10),
                  ticks_x=range(len(cids)), fmt_x=lambda v: hhmm(cids[int(v)]), fmt_y=lambda v: f"{v:g}%", fmt_fim=lambda v: br(v, 1) + "%")


def lotes_br(c):
    cs = coletas(c); out = []
    for a, b in zip(cs, cs[1:]):
        x, y = estado(c, a), estado(c, b); dv = y["vv"] - x["vv"]
        if dv > 0:
            out.append((hhmm(b), (y["f"] - x["f"]) / dv * 100, (y["l"] - x["l"]) / dv * 100, y["f"] - x["f"], y["l"] - x["l"], dv))
    return out


def g05(c):
    L = [l for l in lotes_br(c) if l[0] <= "20:15" and l[5] > 300000]
    itens = [(f"lote das {h}", pf, AZUL if pf >= 49.7 else "#86b6ef") for h, pf, *_ in L]
    return barras_h("05-flavio-em-cada-lote.svg", "Quanto o Flávio fez em cada lote x o que precisava", itens,
                    fmt=lambda v: br(v) + "%", ref=49.7, rotulo_x="% dos válidos de cada lote para o Flávio (linha = 49,7% necessários)",
                    altura_barra=16, vmin=38)


def g06(c):
    return barras_agrupadas("06-palpite-x-projecao.svg", "Palpite das 18:48 x projeção e placar do momento",
                            ["Palpite\n(18:48)", "Projeção por estado\n(18:46)", "Placar\n(18:46)"],
                            [("Flávio", AZUL, [47, 48.16, 50.41]), ("Lula", VERMELHO, [42, 43.88, 41.44])],
                            fmt=lambda v: br(v, 1) + "%")


def g07(c):
    cs = coletas(c)
    itens = []
    for a, b in zip(cs, cs[1:]):
        y, x = estado(c, b), estado(c, a)
        itens.append((f"{hhmm(a)} → {hhmm(b)}", (y["vv"] - x["vv"]) / 1e6, LARANJA if hhmm(b) == "19:14" else CINZA))
    itens = [i for i in itens if i[1] > 0.01][:14]
    return barras_h("07-votos-novos-por-coleta.svg", "Votos válidos novos em cada coleta", itens,
                    fmt=lambda v: br(v) + " mi", rotulo_x="milhões de votos válidos novos entre duas coletas", altura_barra=16)


def g08(c):
    cs = coletas(c); a = next(x for x in cs if x >= "20261004-1914")
    itens = []
    for (uf,) in c.execute("SELECT DISTINCT abrangencia FROM apuracao WHERE coleta_id=? AND abrangencia<>'BR'", (a,)):
        y = estado(c, a, uf)
        rest = y["vv"] / y["frac"] - y["vv"] if y["frac"] else 0
        itens.append((uf, rest * (y["f"] - y["l"]) / y["vv"] / 1e6))
    itens.sort(key=lambda x: x[1])
    itens = [(uf, v, AZUL if v > 0 else VERMELHO) for uf, v in itens if abs(v) > 0.03]
    return barras_h("08-saldo-esperado-por-estado.svg", "Saldo esperado do que faltava apurar, por estado (19:14)", itens,
                    fmt=lambda v: ("+" if v > 0 else "−") + br(abs(v), 2) + " mi", altura_barra=16,
                    rotulo_x="milhões de votos de saldo (azul = Flávio, vermelho = Lula)")


def g09(c):
    L = [l for l in lotes_br(c) if l[0] <= "21:00" and l[5] > 300000]
    itens = [(f"lote das {h}", (f - l) / 1e3, AZUL if f > l else VERMELHO) for h, _, _, f, l, _ in L]
    return barras_h("09-saldo-de-cada-lote.svg", "Saldo de votos de cada atualização (Flávio − Lula)", itens,
                    fmt=lambda v: ("+" if v > 0 else "−") + br(abs(v), 0) + " mil", altura_barra=16,
                    rotulo_x="mil votos de saldo no lote (azul = mais votos ao Flávio, vermelho = ao Lula)")


def g10(c):
    pts_s, pts_b, cs = [], [], coletas(c)
    for i, cid in enumerate(cs):
        u = json.load(open(DADOS / "brutos" / cid / "br-u.json", encoding="utf-8"))
        pts_b.append((i, float(u["s"]["pstn"].replace(",", ".")))); pts_s.append((i, estado(c, cid)["sec"]))
    marca = [i for i, cid in enumerate(cs) if hhmm(cid) in ("18:18", "19:14", "20:06", "21:00")]
    return linhas("10-estados-x-nacional.svg", "% apurado: soma dos estados x arquivo nacional do TSE",
                  [("soma dos 27 estados + exterior", AZUL, pts_s, None), ("arquivo nacional do TSE (o que os sites mostram)", LARANJA, pts_b, None)],
                  "coleta", "% das seções apuradas", (0, len(cs) - 1), (15, 100), ticks_y=range(20, 101, 10),
                  ticks_x=marca, fmt_x=lambda v: hhmm(cs[int(v)]), fmt_y=lambda v: f"{v:g}%", fmt_fim=lambda v: br(v, 1) + "%")


def g11(c):
    cs = coletas(c); a = next(x for x in cs if x >= "20261004-1914"); b = next(x for x in cs if x >= "20261004-2010")
    ufs = ["SP", "MG", "RJ", "BA", "CE", "PE", "MA", "PA"]
    prev, real = [], []
    for uf in ufs:
        x, y = estado(c, a, uf), estado(c, b, uf); dv = y["vv"] - x["vv"]
        prev.append((x["f"] - x["l"]) / x["vv"] * 100); real.append(((y["f"] - x["f"]) - (y["l"] - x["l"])) / dv * 100)
    return barras_agrupadas("11-margem-prevista-x-real.svg", "Margem Flávio − Lula: prevista x real nos votos que entraram depois das 19:14",
                            ufs, [("prevista (acumulado às 19:14)", CINZA, prev), ("real (votos novos 19:14–20:10)", LARANJA, real)],
                            fmt=lambda v: ("+" if v > 0 else "") + br(v, 1))


def g12(c):
    return barras_h("12-estimativas-da-diferenca-final.svg", "Diferença final estimada (Flávio − Lula) por método, às 20:14",
                    [("Reta final como 2022", 1.50, CINZA), ("Projeção corrigida", 2.43, LARANJA), ("Projeção por estado", 2.65, AZUL),
                     ("Tendência de 2026", 2.99, CINZA)], fmt=lambda v: "+" + br(v, 2) + " p.p.",
                    rotulo_x="pontos percentuais a favor do Flávio (0 = empate, as linhas se cruzariam)")


def g13(c):
    return barras_agrupadas("13-palpites-e-projecoes.svg", "Palpites x projeções x placar às 20:26",
                            ["Palpite 1\n(18:48)", "Palpite 2\n(20:27)", "Projeção\npor estado", "Projeção\ncorrigida", "Placar\n20:26"],
                            [("Flávio", AZUL, [47, 47, 47.35, 47.26, 47.98]), ("Lula", VERMELHO, [42, 44, 44.78, 44.88, 44.05])],
                            fmt=lambda v: br(v, 1))


def g14(c):
    s22 = [(x, b - l) for x, b, l in uol22()]
    s26 = [(float(r["secoes_pct"]), float(r["pct_flavio"]) - float(r["pct_lula"])) for r in nacional()]
    return linhas("14-diferenca-2022-x-2026.svg", "Diferença PL − PT ao longo da apuração: 2022 x 2026",
                  [("2026: Flávio − Lula", AZUL, s26, None), ("2022: Bolsonaro − Lula", CINZA, s22, None)],
                  "% das urnas apuradas", "pontos percentuais", (0, 100), (-8, 12), refs=[(0, "empate")],
                  ticks_y=range(-8, 13, 4), ticks_x=range(0, 101, 10), fmt_x=lambda v: f"{v}%",
                  fmt_y=lambda v: ("+" if v > 0 else "") + br(v, 1) if v % 1 else ("+" if v > 0 else "") + f"{v:g}", fmt_fim=lambda v: ("+" if v > 0 else "") + br(v, 1))


def g15(c):
    r18 = list(csv.DictReader(open(DADOS / "historico" / "2018-t2-g1-minuto.csv")))
    fin = int(r18[-1]["validos"])
    s18 = [(int(r["validos"]) / fin * 100, 2 * float(r["pct_bolsonaro"]) - 100) for r in r18 if int(r["validos"]) / fin > .01]
    d2 = json.load(open(DADOS / "uol-historico-2022-t2.json")); t = d2["tuple"]
    s22t2 = [(p[0], p[t.index("candidate22Percent")] - p[t.index("candidate13Percent")]) for p in d2["series"] if p[0] > 1]
    s22 = [(x, b - l) for x, b, l in uol22() if x > 1]
    s26 = [(float(r["secoes_pct"]), float(r["pct_flavio"]) - float(r["pct_lula"])) for r in nacional()]
    return linhas("15-quatro-apuracoes.svg", "Diferença PSL/PL − PT ao longo de quatro apurações",
                  [("2018 2º turno", "#4a3aa7", s18, None), ("2022 1º turno", CINZA, s22, None),
                   ("2022 2º turno", "#1baf7a", s22t2, None), ("2026 1º turno", AZUL, s26, None)],
                  "% apurado", "pontos percentuais", (0, 100), (-8, 26), refs=[(0, "empate")],
                  ticks_y=range(-5, 26, 5), ticks_x=range(0, 101, 10), fmt_x=lambda v: f"{v}%",
                  fmt_y=lambda v: ("+" if v > 0 else "") + br(v, 1) if v % 1 else ("+" if v > 0 else "") + f"{v:g}", fmt_fim=lambda v: ("+" if v > 0 else "") + br(v, 1))


def g16(c):
    t = list(csv.DictReader(open(DADOS / "historico" / "presidente_turnos.csv")))
    anos = sorted({int(r["ano"]) for r in t})
    p = lambda turno: [float(r["pct_abstencao"]) for a in anos for r in t if int(r["ano"]) == a and int(r["turno"]) == turno]
    return barras_agrupadas("16-abstencao-por-ano.svg", "Abstenção na eleição presidencial, 1º e 2º turno (% do eleitorado)",
                            [str(a) for a in anos] + ["2026"],
                            [("1º turno", CINZA, p(1) + [21.01]), ("2º turno", LARANJA, p(2) + [0])], fmt=lambda v: br(v, 1) if v else "?")


def g17(c):
    F, L = 47.26, 44.88; O = 100 - F - L
    itens = []
    for s in (40, 50, 60, 65, 70):
        f2, l2 = F + O * (1 - s / 100), L + O * s / 100
        d = (f2 - l2) / (f2 + l2) * 100
        itens.append((f"Lula com {s}% dos outros", d, AZUL if d > 0.05 else (CINZA if abs(d) <= .05 else VERMELHO)))
    return barras_h("17-cenarios-segundo-turno.svg", "2º turno: diferença final conforme a divisão dos votos dos outros candidatos",
                    itens, fmt=lambda v: ("Flávio +" if v > 0.05 else "Lula +" if v < -0.05 else "empate ") + br(abs(v), 1),
                    rotulo_x="diferença em p.p. (azul = Flávio vence, vermelho = Lula vence)", altura_barra=20)


def g18(c):
    v = list(csv.DictReader(open(DADOS / "historico" / "presidente_votos_uf.csv")))
    from collections import defaultdict
    nac, mg = defaultdict(lambda: defaultdict(int)), defaultdict(lambda: defaultdict(int))
    for r in v:
        k = (r["ano"], r["turno"]); nac[k][r["partido"]] += int(r["votos"])
        if r["uf"] == "MG":
            mg[k][r["partido"]] += int(r["votos"])
    cats, s_br, s_mg = [], [], []
    for k in sorted(nac):
        d = nac[k]; top = sorted(d, key=lambda p: -d[p])[:2]
        sb = (d[top[0]] - d[top[1]]) / sum(d.values()) * 100
        m = mg[k]; sm = (m[top[0]] - m[top[1]]) / sum(m.values()) * 100
        cats.append(f"{k[0]}\n{k[1]}º t."); s_br.append(sb); s_mg.append(sm)
    return barras_agrupadas("18-minas-x-brasil.svg", "Vantagem do vencedor nacional: no Brasil x em Minas (p.p.)", cats,
                            [("Brasil", CINZA, s_br), ("Minas Gerais", LARANJA, s_mg)], fmt=lambda v: br(v, 0), h=360)


def g19(c):
    cs = coletas(c); pts = []
    for i, cid in enumerate(cs):
        u = json.load(open(DADOS / "brutos" / cid / "br-u.json", encoding="utf-8"))
        pts.append((i, float(u["s"]["pstn"].replace(",", ".")), u.get("md")))
    antes = [(i, v) for i, v, md in pts if md != "s"]; depois = [(i, v) for i, v, md in pts if md == "s"]
    if antes and depois:
        depois = [antes[-1]] + depois
    marca = [i for i, cid in enumerate(cs) if hhmm(cid) in ("18:18", "19:14", "20:06", "20:58")]
    return linhas("19-matematicamente-definido.svg", "Arquivo nacional do TSE: % apurado e o momento em que a eleição ficou definida",
                  [("ainda indefinido (md = n)", CINZA, antes, None), ("matematicamente definido (md = s)", LARANJA, depois, None)],
                  "coleta", "% das seções no arquivo nacional", (0, len(cs) - 1), (15, 100), ticks_y=range(20, 101, 10),
                  ticks_x=marca, fmt_x=lambda v: hhmm(cs[int(v)]), fmt_y=lambda v: f"{v:g}%", fmt_fim=lambda v: br(v, 1) + "%")


def g20(c):
    cid = next(x for x in coletas(c) if x >= "20261004-2132")
    itens = []
    for (uf,) in c.execute("SELECT DISTINCT abrangencia FROM apuracao WHERE coleta_id=? AND abrangencia<>'BR'", (cid,)):
        y = estado(c, cid, uf)
        rest = y["vv"] / y["frac"] - y["vv"] if y["frac"] else 0
        if rest > 500:
            itens.append((uf, rest / 1e3, AZUL if y["f"] > y["l"] else VERMELHO))
    itens.sort(key=lambda x: -x[1])
    return barras_h("20-o-que-faltava-1132.svg", "Votos válidos que faltavam por estado às 21:32 (cor = quem lidera no estado)",
                    itens, fmt=lambda v: br(v, 0) + " mil", rotulo_x="mil votos válidos ainda não apurados", altura_barra=15)


def g21(c):
    import municipios as mu
    rows = mu.ler()
    base = mu.margem([r for r in rows if r["pct_soja_territorio"] == 0])
    viz = mu.vs_vizinhos(rows)
    faixas = mu.FAIXAS[1:]
    pais = [mu.margem([r for r in rows if mu.faixa(r["pct_soja_territorio"]) == f]) - base for f in faixas]
    return barras_agrupadas("21-soja-pais-x-estado.svg",
                            "Quanto a margem PL − PT é maior que nos municípios sem soja (p.p.), por faixa de soja no território",
                            [f"soja\n{f}" for f in faixas],
                            [("contra os sem soja do país todo", CINZA, pais),
                             ("contra os sem soja do mesmo estado e porte", LARANJA, [viz[f][0] for f in faixas])],
                            fmt=lambda v: ("+" if v > 0 else "") + br(v, 1), h=340)


def g21b(c):
    import municipios as mu
    ne = [r for r in mu.ler() if r["regiao"] == "Nordeste" and r["soja_ha_2025"] > 0]
    vmax = max(r["validos_2026"] for r in ne)
    pts = [(min(r["pct_soja_territorio"], 62), r["margem_2026_pp"], 1.6 + 10 * (r["validos_2026"] / vmax) ** .5,
            AZUL if r["margem_2026_pp"] > 0 else VERMELHO) for r in ne]
    lugar = {(r["municipio"], r["uf"]): r for r in ne}
    rot = []
    for (nm, uf), dx, dy in [(("Luís Eduardo Magalhães", "BA"), -14, 4), (("Balsas", "MA"), 12, 4),
                             (("São Desidério", "BA"), 12, 4), (("Formosa do Rio Preto", "BA"), -12, -8),
                             (("Barreiras", "BA"), -14, -10), (("Baixa Grande do Ribeiro", "PI"), 12, -6),
                             (("Riachão das Neves", "BA"), 10, 4)]:
        r = lugar[(nm, uf)]
        rot.append((r["pct_soja_territorio"], r["margem_2026_pp"], f"{nm} ({uf})", dx, dy))
    ne_todo = mu.margem([r for r in mu.ler() if r["regiao"] == "Nordeste"])
    ymin = min(-80, min(p[1] for p in pts))
    return dispersao("21-nordeste-soja.svg",
                     "Nordeste: municípios que plantam soja, por % do território com soja e margem PL − PT no 1º turno de 2026",
                     pts, "% do território do município plantado com soja (2025)", "margem PL − PT (p.p.)",
                     (0, 62), (ymin, 40), range(0, 61, 10), range(-80, 41, 20),
                     fmt_x=lambda v: f"{v:g}%", fmt_y=lambda v: ("+" if v > 0 else "") + f"{v:g}",
                     refs=[(ne_todo, f"Nordeste inteiro: {br(ne_todo, 1)}")], rotulos=rot,
                     notas=[("PL venceu", AZUL), ("PT venceu", VERMELHO), ("tamanho = votos válidos", CINZA)])


def main():
    c = con()
    feitos = []
    for g in (g01, g03, g04, g05, g06, g07, g08, g09, g10, g11, g12, g13, g14, g15, g16, g17, g18, g19, g20, g21, g21b):
        try:
            feitos.append(g(c))
        except Exception as e:
            print(f"  ! {g.__name__}: {e}")
    print(f"gráficos: {len(feitos)} SVGs em cases/graficos/")


if __name__ == "__main__":
    main()
