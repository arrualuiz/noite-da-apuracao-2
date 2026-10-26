#!/usr/bin/env python3
"""As denúncias do 2º turno (transporte, chuva, horário) aparecem nos dados?

No 2º turno de 2026 houve denúncias de falta de ônibus em 8 estados (BA, SP, PI, SE, PA, AL, RJ, PB, segundo o
Ministério da Justiça), de chuva no PR, em SC e em SP (pedido da campanha do Flávio) e uma decisão do STF
estendendo a votação até as 19h. Aqui, três testes:

1. Horário: o boletim de cada urna registra a abertura e o encerramento. Numa amostra de urnas das cidades
   citadas nas denúncias (e em todas as de Curitiba), a que horas as urnas fecharam, no 1º e no 2º turno?
2. Estados: quanto a abstenção mudou do 1º para o 2º turno em 2026, comparado com o que costuma mudar
   (2002 a 2022, dados/crescimento.csv).
3. Cidades: a mudança do 1º para o 2º turno em 2026 x a mesma mudança em 2022, cidade por cidade
   (detalhe_votacao_munzona_2022 do TSE). Quem piorou muito mais que em 2022 é candidato a ter tido problema.

Gera dados/acesso_horarios.csv e dados/acesso_municipios.csv.
Uso: python3 analise/acesso.py
"""
import csv
import io
import json
import random
import re
import zipfile
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from bairros import bu, secoes

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "dados"
CACHES = [PASTA / "historico" / "tse", RAIZ.parent / "xx-noite-do-primeiro-turno-2026" / "dados" / "historico" / "tse"]
PLEITOS = {1: "3220", 2: "3221"}
AMOSTRA = 150  # urnas por cidade (Curitiba entra inteira, porque os boletins já estão baixados)
CIDADES = [("sp", "71072", "São Paulo"), ("sp", "64777", "Guarulhos"), ("ba", "38490", "Salvador"), ("pi", "12190", "Teresina"),
           ("pa", "04278", "Belém"), ("rj", "60011", "Rio de Janeiro"), ("rj", "58653", "Niterói"), ("rj", "58971", "São Gonçalo"),
           ("pb", "20516", "João Pessoa"), ("se", "31054", "Aracaju"), ("al", "27855", "Maceió"), ("sc", "81051", "Florianópolis"),
           ("pr", "75353", "Curitiba")]
DENUNCIA_TRANSPORTE = {"BA", "SP", "PI", "SE", "PA", "AL", "RJ", "PB"}
DENUNCIA_CHUVA = {"PR", "SC", "SP"}


def encerramento(b):
    """Abertura e encerramento da urna: as duas últimas datas aaaammddThhmmss do boletim."""
    h = re.findall(rb"20\d{6}T(\d{6})", b)
    return (h[-2].decode(), h[-1].decode()) if len(h) >= 2 else (None, None)


def horarios():
    linhas = []
    for uf, mun, nome in CIDADES:
        for turno, pleito in PLEITOS.items():
            lista = secoes(uf, mun, pleito)
            if mun != "75353" and len(lista) > AMOSTRA:
                lista = random.Random(2026).sample(lista, AMOSTRA)  # a mesma amostra nos dois turnos
            with ThreadPoolExecutor(max_workers=8) as ex:
                bus = list(ex.map(lambda zs: (zs, bu(uf, mun, pleito, *zs)), lista))
            for (zona, sec), b in bus:
                if b:
                    ab, fim = encerramento(b)
                    linhas.append({"cidade": nome, "uf": uf.upper(), "turno": turno, "zona": zona, "secao": sec, "abertura": ab, "encerramento": fim})
        print(f"  {nome}: boletins lidos")
    with (PASTA / "acesso_horarios.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    print("\n1. A QUE HORAS AS URNAS FECHARAM (boletim de urna; amostra de 150 urnas por cidade, Curitiba inteira)\n")
    print(f"   {'cidade':16}{'turno':>6}{'urnas':>7}   {'mediana':>8}{'última':>8}   {'até 17h29':>10}{'17h30–18h59':>13}{'19h ou depois':>15}")
    for _, _, nome in CIDADES:
        for t in (1, 2):
            fims = sorted(l["encerramento"] for l in linhas if l["cidade"] == nome and l["turno"] == t and l["encerramento"])
            if not fims:
                continue
            c = Counter("a" if f < "173000" else "b" if f < "190000" else "c" for f in fims)
            hm = lambda x: f"{x[:2]}h{x[2:4]}"
            print(f"   {nome:16}{t:>5}º{len(fims):>7}   {hm(fims[len(fims) // 2]):>8}{hm(fims[-1]):>8}   {c['a']:>10}{c['b']:>13}{c['c']:>15}")


def estados():
    hist = defaultdict(dict)
    for r in csv.DictReader((PASTA / "crescimento.csv").open(encoding="utf-8")):
        if r["nivel"] in ("Estado", "Brasil") and r["abstencoes_1t"] and r["abstencoes_2t"]:
            d = int(r["abstencoes_2t"]) / int(r["aptos_2t"]) * 100 - int(r["abstencoes_1t"]) / int(r["aptos_1t"]) * 100
            hist[r["uf"] or "BR"][int(r["ano"])] = (d, int(r["abstencoes_2t"]) - int(r["abstencoes_1t"]))
    print("\n2. ABSTENÇÃO DO 1º PARA O 2º TURNO, POR ESTADO: 2026 x O QUE COSTUMA ACONTECER (2002 a 2022)\n")
    print(f"   {'':4}{'2026':>9}{'pessoas':>11}   {'média 2002–22':>14}{'2022':>8}   {'2026 − média':>13}   denúncia")
    linhas = []
    for uf, anos in hist.items():
        if 2026 not in anos:
            continue
        antes = [d for a, (d, _) in anos.items() if a < 2026]
        media = sum(antes) / len(antes)
        linhas.append((anos[2026][0] - media, uf, anos[2026], media, anos.get(2022, (None,))[0]))
    for dif, uf, (d26, p26), media, d22 in sorted(linhas):
        den = ", ".join(x for x, s in (("transporte", DENUNCIA_TRANSPORTE), ("chuva", DENUNCIA_CHUVA)) if uf in s)
        print(f"   {uf:4}{d26:+8.2f}{p26:>+11,}   {media:+13.2f}{d22:+8.2f}   {dif:+12.2f}   {den}".replace(",", "."))


def municipios():
    """2026 (dados/abstencao_municipios.csv) x 2022 (detalhe_votacao_munzona_2022), cidade por cidade."""
    arq = next(p / "detalhe_votacao_munzona_2022.zip" for p in CACHES if (p / "detalhe_votacao_munzona_2022.zip").exists())
    z = zipfile.ZipFile(arq)
    nome = next(n for n in z.namelist() if n.endswith("_BRASIL.csv"))
    a22 = defaultdict(lambda: defaultdict(int))
    with z.open(nome) as fh:
        for r in csv.DictReader(io.TextIOWrapper(fh, encoding="latin-1"), delimiter=";"):
            if r["CD_CARGO"] == "1":
                k = r["CD_MUNICIPIO"].zfill(5)
                a22[k][f"aptos{r['NR_TURNO']}"] += int(r["QT_APTOS"])
                a22[k][f"abst{r['NR_TURNO']}"] += int(r["QT_ABSTENCOES"])
    out = []
    for r in csv.DictReader((PASTA / "abstencao_municipios.csv").open(encoding="utf-8")):
        x = a22.get(r["cd_tse"])
        if r["uf"] == "ZZ" or not x or not x["aptos1"] or not x["aptos2"] or not r["pct_abstencao"] or not r["pct_abstencao_1t"]:
            continue
        d22 = x["abst2"] / x["aptos2"] * 100 - x["abst1"] / x["aptos1"] * 100
        d26 = float(r["pct_abstencao"]) - float(r["pct_abstencao_1t"])
        out.append({"uf": r["uf"], "cd_tse": r["cd_tse"], "municipio": r["municipio"], "eleitorado": int(r["eleitorado"]),
                    "dif_2026_pts": round(d26, 2), "dif_2022_pts": round(d22, 2), "a_mais_que_2022_pts": round(d26 - d22, 2),
                    "pessoas_2026": int(r["abstencao"]) - int(r["abstencao_1t"])})
    with (PASTA / "acesso_municipios.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print("\n3. CIDADES DAS DENÚNCIAS: abstenção do 1º para o 2º turno em 2026 x em 2022 (pontos)\n")
    print(f"   {'cidade':22}{'2026':>8}{'2022':>8}{'diferença':>11}{'pessoas 2026':>14}")
    por = {o["cd_tse"]: o for o in out}
    for uf, mun, nome in CIDADES:
        o = por.get(mun)
        if o:
            print(f"   {nome:22}{o['dif_2026_pts']:+8.2f}{o['dif_2022_pts']:+8.2f}{o['a_mais_que_2022_pts']:+11.2f}{o['pessoas_2026']:>+14,}".replace(",", "."))
    grandes = [o for o in out if o["eleitorado"] >= 100_000]
    print("\n   Cidades de 100 mil eleitores ou mais em que a abstenção mais piorou em relação a 2022:")
    for o in sorted(grandes, key=lambda o: -o["a_mais_que_2022_pts"])[:10]:
        print(f"   {o['municipio'][:22]:22}{o['uf']:>3}{o['dif_2026_pts']:+8.2f}{o['dif_2022_pts']:+8.2f}{o['a_mais_que_2022_pts']:+11.2f}{o['pessoas_2026']:>+14,}".replace(",", "."))
    n = len(out)
    print(f"\n   Em {sum(o['dif_2026_pts'] < 0 for o in out)} de {n} cidades a abstenção caiu do 1º para o 2º turno em 2026;"
          f" em 2022, em {sum(o['dif_2022_pts'] < 0 for o in out)} de {n}.")


def main():
    horarios()
    estados()
    municipios()


if __name__ == "__main__":
    main()
