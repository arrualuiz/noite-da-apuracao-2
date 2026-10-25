#!/usr/bin/env python3
"""Histórico oficial das eleições presidenciais 2002–2022 a partir dos dados abertos do TSE.

Uso: python3 analise/historico_tse.py

Baixa (com cache em dados/historico/tse/, fora do git):
  - detalhe_votacao_munzona_<ano>.zip  (~4 MB): aptos, comparecimento, abstenção, brancos, nulos
  - votacao_partido_munzona_<ano>.zip: só o arquivo *_BR.csv (Presidente), lido por download
    parcial (HTTP Range), sem baixar o zip inteiro
Gera:
  dados/historico/presidente_turnos.csv    ano × turno: aptos, comparecimento, abstenção, brancos, nulos, válidos
  dados/historico/presidente_votos.csv     ano × turno × candidato (partido): votos e % dos válidos
  dados/historico/presidente_votos_uf.csv  ano × turno × UF × candidato (partido): votos
"""
import csv
import io
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "dados" / "historico" / "tse"
SAIDA = RAIZ / "dados" / "historico"
ANOS = [2002, 2006, 2010, 2014, 2018, 2022]
CDN = "https://cdn.tse.jus.br/estatistica/sead/odsele"


class ArquivoRemoto(io.RawIOBase):
    """Arquivo HTTP lido por pedaços (Range), para abrir um zip remoto sem baixá-lo inteiro."""

    def __init__(self, url):
        self.url, self.pos = url, 0
        r = urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=60)
        self.size = int(r.headers["Content-Length"])

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos

    def readinto(self, b):
        if self.pos >= self.size:
            return 0
        fim = min(self.pos + len(b), self.size) - 1
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{fim}"})
        dados = urllib.request.urlopen(req, timeout=120).read()
        b[:len(dados)] = dados
        self.pos += len(dados)
        return len(dados)


def linhas_csv(fh):
    return csv.DictReader(io.TextIOWrapper(fh, encoding="latin-1"), delimiter=";")


def detalhe(ano):
    """Totais de Presidente por turno (soma de todas as zonas, Brasil e exterior)."""
    arq = CACHE / f"detalhe_votacao_munzona_{ano}.zip"
    if not arq.exists():
        urllib.request.urlretrieve(f"{CDN}/detalhe_votacao_munzona/detalhe_votacao_munzona_{ano}.zip", arq)
    z = zipfile.ZipFile(arq)
    nome = next(n for n in z.namelist() if n.endswith("_BRASIL.csv"))
    tot = defaultdict(lambda: defaultdict(int))
    campos = ["QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES", "QT_VOTOS_BRANCOS", "QT_TOTAL_VOTOS_NULOS",
              "QT_TOTAL_VOTOS_VALIDOS"]
    with z.open(nome) as fh:
        for r in linhas_csv(fh):
            if r["CD_CARGO"] != "1":
                continue
            for c in campos:
                tot[int(r["NR_TURNO"])][c] += int(r[c] or 0)
    return tot


def votos(ano):
    """Votos de Presidente por turno e partido (só o *_BR.csv do zip remoto)."""
    url = f"{CDN}/votacao_partido_munzona/votacao_partido_munzona_{ano}.zip"
    z = zipfile.ZipFile(ArquivoRemoto(url))
    nome = next(n for n in z.namelist() if n.endswith("_BR.csv"))
    tot, uf = defaultdict(int), defaultdict(int)
    with z.open(nome) as fh:
        for r in linhas_csv(fh):
            if r["CD_CARGO"] != "1":
                continue
            v = int(r.get("QT_VOTOS_NOMINAIS_VALIDOS") or r.get("QT_VOTOS_NOMINAIS") or 0)
            chave = (int(r["NR_TURNO"]), int(r["NR_PARTIDO"]), r["SG_PARTIDO"])
            tot[chave] += v
            uf[(chave[0], r["SG_UF"], chave[1], chave[2])] += v
    return tot, uf


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    turnos, cands, por_uf = [], [], []
    for ano in ANOS:
        d = detalhe(ano)
        for t in sorted(d):
            x = d[t]
            turnos.append([ano, t, x["QT_APTOS"], x["QT_COMPARECIMENTO"], x["QT_ABSTENCOES"],
                           round(x["QT_ABSTENCOES"] / x["QT_APTOS"] * 100, 2),
                           x["QT_VOTOS_BRANCOS"], x["QT_TOTAL_VOTOS_NULOS"], x["QT_TOTAL_VOTOS_VALIDOS"]])
        v, vu = votos(ano)
        por_uf += [[ano, t, u, num, sg, n] for (t, u, num, sg), n in sorted(vu.items())]
        validos = defaultdict(int)
        for (t, _, _), n in v.items():
            validos[t] += n
        for (t, num, sg), n in sorted(v.items(), key=lambda kv: (kv[0][0], -kv[1])):
            cands.append([ano, t, num, sg, n, round(n / validos[t] * 100, 2)])
        print(f"{ano}: " + " | ".join(f"{t}º turno abst {r[5]}%" for r in turnos if r[0] == ano for t in [r[1]]))
    with (SAIDA / "presidente_turnos.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ano", "turno", "aptos", "comparecimento", "abstencoes", "pct_abstencao", "brancos", "nulos", "validos"])
        w.writerows(turnos)
    with (SAIDA / "presidente_votos.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ano", "turno", "numero", "partido", "votos", "pct_validos"])
        w.writerows(cands)
    with (SAIDA / "presidente_votos_uf.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ano", "turno", "uf", "numero", "partido", "votos"])
        w.writerows(por_uf)
    print("histórico: dados/historico/presidente_turnos.csv, presidente_votos.csv e presidente_votos_uf.csv")


if __name__ == "__main__":
    main()
