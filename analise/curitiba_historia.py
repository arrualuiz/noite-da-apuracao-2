#!/usr/bin/env python3
"""Curitiba por bairro em todas as eleições do PT (2002 a 2026), cruzada com o Censo 2022 por bairro.

1. Voto: votacao_secao_<ano>_BR.zip (dados abertos do TSE: Presidente por seção, com o número do local de votação).
2. Bairro de cada seção, na ordem:
   a. a coordenada do local de votação (eleitorado_local_votacao_<ano>, de 2010 em diante) cai num dos
      75 polígonos do IPPUC (dados/curitiba-bairros.topo.json);
   b. o nome do bairro escrito no cadastro do local bate com um bairro oficial;
   c. o mesmo local (zona + número) em outro ano já tem bairro. É assim que 2002 e 2006 entram, porque
      esses anos não têm o arquivo de locais.
   2026 vem de dados/curitiba_secoes.csv (analise/bairros.py).
3. Censo 2022 por bairro (IBGE, Agregados por bairros): renda média e mediana do responsável pelo domicílio,
   % de pessoas de 15 anos ou mais alfabetizadas e % de pessoas brancas.

Gera dados/curitiba_bairros_historia.csv (bairro x ano) e dados/curitiba_bairros_censo.csv, e mostra a
correlação entre a renda do bairro e o voto no PT em cada eleição.

Uso: python3 analise/curitiba_historia.py   (downloads do TSE e do IBGE ficam em dados/historico/, fora do git)
"""
import csv
import io
import math
import unicodedata
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

from bairros import dentro, malha, nome_proprio

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "dados"
TSE = PASTA / "historico" / "tse"
CENSO = PASTA / "historico" / "ibge" / "censo2022"
CDN = "https://cdn.tse.jus.br/estatistica/sead/odsele"
IBGE = "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022"
CURITIBA_TSE, CURITIBA_IBGE = "75353", "4106902"
ANOS = [2002, 2006, 2010, 2014, 2018, 2022]
RIVAL = {2002: 45, 2006: 45, 2010: 45, 2014: 45, 2018: 17, 2022: 22}  # número do rival no 2º turno
CENSO_ARQS = {
    "renda": "Agregados_por_Setores_Censitarios_Rendimento_do_Responsavel/Agregados_por_bairros_renda_responsavel_BR_20260508_csv.zip",
    "alfabetizacao": "Agregados_por_Setores_Censitarios/Agregados_por_Bairro_csv/Agregados_por_bairros_alfabetizacao_BR.zip",
    "demografia": "Agregados_por_Setores_Censitarios/Agregados_por_Bairro_csv/Agregados_por_bairros_demografia_BR.zip",
    "cor": "Agregados_por_Setores_Censitarios/Agregados_por_Bairro_csv/Agregados_por_bairros_cor_ou_raca_BR.zip",
    "basico": "Agregados_por_Setores_Censitarios/Agregados_por_Bairro_csv/Agregados_por_bairros_basico_BR_20260520.zip",
}


MESMO_BAIRRO = {"BOTIATUVINHA": "BUTIATUVINHA"}  # grafia do IBGE -> grafia do IPPUC


def baixar(url, destino):
    if not destino.exists():
        destino.parent.mkdir(parents=True, exist_ok=True)
        print(f"  baixando {destino.name}…")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=600) as r, open(destino.with_suffix(".parcial"), "wb") as fh:
            while bloco := r.read(1 << 20):
                fh.write(bloco)
        destino.with_suffix(".parcial").rename(destino)
    return destino


def chave(s):
    return " ".join(unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper().split())


def ler_zip(arq, filtro=None):
    """Linhas de cada CSV do zip (latin-1, separado por ;)."""
    z = zipfile.ZipFile(arq)
    for n in z.namelist():
        if n.endswith(".csv") and (filtro is None or filtro(n)):
            with z.open(n) as fh:
                yield from csv.DictReader(io.TextIOWrapper(fh, encoding="latin-1"), delimiter=";")


def locais(bairros):
    """(zona, local) -> bairro oficial, de cada ano com arquivo de locais (2010 a 2026), e o caminho usado."""
    por_ano, qualquer = {}, {}
    oficiais = {chave(b): b for b, _, _ in bairros}

    def bairro_de(r):
        try:
            lat, lon = float(r["NR_LATITUDE"].replace(",", ".")), float(r["NR_LONGITUDE"].replace(",", "."))
            if lat != -1:
                achou = next((b for b, _, an in bairros if dentro(lon, lat, an)), None)
                if achou:
                    return achou, "mapa"
        except (KeyError, ValueError):
            pass
        k = chave(r.get("NM_BAIRRO", ""))
        if k:
            achou = oficiais.get(k) or next((v for kk, v in oficiais.items() if kk.startswith(k) or k.startswith(kk)), None)
            if achou:
                return achou, "nome"
        return None, None

    for ano in [2010, 2014, 2018, 2022, 2026]:
        arq = TSE / "locais" / f"eleitorado_local_votacao_{ano}.zip"
        baixar(f"{CDN}/eleitorado_locais_votacao/eleitorado_local_votacao_{ano}.zip", arq)
        d = {}
        for r in ler_zip(arq, lambda n: n.endswith(("_PR.csv", f"_{ano}.csv"))):
            if r.get("CD_MUNICIPIO") != CURITIBA_TSE:
                continue
            k = (int(r["NR_ZONA"]), int(r["NR_LOCAL_VOTACAO"]))
            if k not in d:
                d[k] = bairro_de(r)
        por_ano[ano] = d
        for k, v in d.items():
            if v[0]:
                qualquer[k] = v[0]  # o ano mais recente fica por último
        print(f"  locais {ano}: {len(d)} em Curitiba, {sum(1 for v in d.values() if v[0])} com bairro")
    return por_ano, qualquer


def votos(ano):
    """(turno, zona, local) -> {pt, rival, validos} de Presidente em Curitiba."""
    # Presidente por seção fica no arquivo do Brasil (o de cada estado só tem os cargos estaduais)
    arq = baixar(f"{CDN}/votacao_secao/votacao_secao_{ano}_BR.zip", TSE / "secao" / f"votacao_secao_{ano}_BR.zip")
    out = defaultdict(lambda: defaultdict(int))
    for r in ler_zip(arq):
        if r["CD_MUNICIPIO"] != CURITIBA_TSE or r["CD_CARGO"] != "1":
            continue
        n, q = int(r["NR_VOTAVEL"]), int(r["QT_VOTOS"])
        x = out[(int(r["NR_TURNO"]), int(r["NR_ZONA"]), int(r.get("NR_LOCAL_VOTACAO") or 0))]
        if n in (95, 96, 97):  # branco, nulo, anulado
            continue
        x["validos"] += q
        if n == 13:
            x["pt"] += q
        elif n == RIVAL[ano]:
            x["rival"] += q
    return out


def censo(bairros):
    """Censo 2022 por bairro oficial de Curitiba."""
    oficiais = {chave(b): b for b, _, _ in bairros}
    linhas = defaultdict(dict)
    for nome, caminho in CENSO_ARQS.items():
        arq = baixar(f"{IBGE}/{caminho}", CENSO / Path(caminho).name)
        for r in ler_zip(arq):
            cd = r.get("CD_BAIRRO", "")
            if not cd.startswith(CURITIBA_IBGE):
                continue
            nm = MESMO_BAIRRO.get(chave(r["NM_BAIRRO"]), chave(r["NM_BAIRRO"]))
            b = oficiais.get(nm) or next((v for k, v in oficiais.items() if k.startswith(nm)), None)
            if b:
                linhas[b].update({f"{nome}:{k}": v for k, v in r.items()})
    num = lambda v: float(v.replace(",", ".")) if v not in ("", ".", "X", None) else None
    out = {}
    for b, r in linhas.items():
        g = lambda k: num(r.get(k))
        alf = sum(g(f"alfabetizacao:V00{n}") or 0 for n in range(644, 657))   # alfabetizados, 15 anos ou mais
        pop15 = sum(g(f"demografia:V010{n}") or 0 for n in range(34, 42))     # moradores de 15 anos ou mais
        brancos = g("cor:V01317")
        total_cor = sum(g(f"cor:V013{n}") or 0 for n in range(17, 22))        # branca, preta, amarela, parda, indígena
        out[b] = {"bairro": b, "populacao": g("basico:v0001"), "renda_media": g("renda:V06004"), "renda_mediana": g("renda:V06006"),
                  "pct_alfabetizados_15mais": round(alf / pop15 * 100, 2) if pop15 else None,
                  "pct_brancos": round(brancos / total_cor * 100, 2) if brancos and total_cor else None}
    return out


def correlacao(xs, ys, ws):
    mx, my, sw = (sum(w * x for x, w in zip(xs, ws)) / sum(ws), sum(w * y for y, w in zip(ys, ws)) / sum(ws), sum(ws))
    cov = sum(w * (x - mx) * (y - my) for x, y, w in zip(xs, ys, ws)) / sw
    vx, vy = (sum(w * (x - mx) ** 2 for x, w in zip(xs, ws)) / sw, sum(w * (y - my) ** 2 for y, w in zip(ys, ws)) / sw)
    return cov / math.sqrt(vx * vy)


def main():
    bairros = malha("curitiba")
    por_ano, qualquer = locais(bairros)
    hist = defaultdict(lambda: defaultdict(int))
    for ano in ANOS:
        v = votos(ano)
        sem = com = 0
        for (t, z, l), x in v.items():
            b = (por_ano.get(ano, {}).get((z, l)) or (None,))[0] or qualquer.get((z, l))
            if not b:
                sem += x["validos"]
                b = "(sem bairro)"
            else:
                com += x["validos"]
            for k, q in x.items():
                hist[(ano, b)][f"{k}_{t}t"] += q
        print(f"{ano}: {com / (com + sem) * 100:.1f}% dos votos válidos com bairro")
    for r in csv.DictReader((PASTA / "curitiba_bairros.csv").open(encoding="utf-8")):
        h = hist[(2026, r["bairro"])]
        h.update({"pt_1t": int(r["lula_1t"]), "rival_1t": int(r["flavio_1t"]), "pt_2t": int(r["lula_2t"]), "rival_2t": int(r["flavio_2t"]),
                  "validos_1t": sum(int(r[k]) for k in ("lula_1t", "flavio_1t", "cury_1t", "renan_1t", "caiado_1t", "outros_1t")),
                  "validos_2t": int(r["lula_2t"]) + int(r["flavio_2t"])})
    campos = ["pt_1t", "rival_1t", "validos_1t", "pt_2t", "rival_2t", "validos_2t"]
    with (PASTA / "curitiba_bairros_historia.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ano", "bairro"] + campos)
        for (ano, b), h in sorted(hist.items()):
            w.writerow([ano, b] + [h.get(k, 0) for k in campos])

    c = censo(bairros)
    with (PASTA / "curitiba_bairros_censo.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(next(iter(c.values()))))
        w.writeheader()
        w.writerows(sorted(c.values(), key=lambda x: x["bairro"]))
    print(f"\nCenso 2022: {len(c)} bairros de Curitiba · ex.: " +
          ", ".join(f"{b} R$ {x['renda_media']:,.0f}".replace(",", ".") for b, x in sorted(c.items(), key=lambda kv: -(kv[1]['renda_media'] or 0))[:3]))

    print("\nCorrelação (ponderada pelos votos) entre a renda média do bairro (log) e o PT no 2º turno:")
    for ano in ANOS + [2026]:
        xs, ys, ws = [], [], []
        for (a, b), h in hist.items():
            if a == ano and b in c and c[b]["renda_media"] and h.get("pt_2t", 0) + h.get("rival_2t", 0) > 500:
                xs.append(math.log(c[b]["renda_media"]))
                ys.append(h["pt_2t"] / (h["pt_2t"] + h["rival_2t"]) * 100)
                ws.append(h["pt_2t"] + h["rival_2t"])
        if len(xs) > 5:
            print(f"  {ano}: r = {correlacao(xs, ys, ws):+.2f}  ({len(xs)} bairros)")


if __name__ == "__main__":
    main()
