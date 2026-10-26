#!/usr/bin/env python3
"""Uma cidade por bairro, nos dois turnos, a partir do boletim de cada urna.

1. Lista as seções da cidade (arquivo-urna/<pleito>/config/<uf>/<uf>-p<pleito>-cs.json) e baixa o
   boletim de urna (.bu) de cada uma, nos dois turnos. Os boletins ficam em
   dados/historico/tse/bu/<pleito>/<uf><cidade>/ (fora do git; só baixa o que ainda não tem).
2. Lê cada boletim (ASN.1/DER, lido aqui sem biblioteca): aptos, quem foi votar, votos de cada
   candidato a presidente, brancos e nulos.
3. Liga cada seção ao bairro do local de votação, pelos dados abertos do TSE
   (eleitorado_local_votacao_2026, em dados/historico/tse/locais/).

Gera dados/<nome>_secoes.csv e dados/<nome>_bairros.csv.

Uso: python3 analise/bairros.py                       # Curitiba
     python3 analise/bairros.py pr 75353 curitiba     # uf, código TSE da cidade, nome do arquivo
"""
import csv
import io
import json
import sys
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "dados"
TSE = PASTA / "historico" / "tse"
URNA = "https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna/{p}/"
PLEITOS = {1: ("3220", 6257), 2: ("3221", 6258)}  # turno: (pleito, eleição de presidente)
NUM = {13: "lula", 22: "flavio", 70: "cury", 14: "renan", 55: "caiado"}


def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


# --- leitor de DER (só o que o boletim usa: tag, tamanho, valor) ---
def tlv(b, i):
    t = b[i]
    i += 1
    num = t & 0x1F
    if num == 0x1F:
        num = 0
        while True:
            c = b[i]
            i += 1
            num = (num << 7) | (c & 0x7F)
            if not c & 0x80:
                break
    n = b[i]
    i += 1
    if n & 0x80:
        k = n & 0x7F
        n = int.from_bytes(b[i:i + k], "big")
        i += k
    return t, num, i, n


def filhos(b, i=0, fim=None):
    """Elementos de um nível: (classe, número, construído, valor em bytes)."""
    fim = len(b) if fim is None else fim
    out = []
    while i < fim:
        t, num, j, n = tlv(b, i)
        out.append((t >> 6, num, bool(t & 0x20), b[j:j + n]))
        i = j + n
    return out


def inteiro(v):
    return int.from_bytes(v, "big", signed=True)


def ler_bu(b, eleicao):
    """Do boletim: local e seção (do envelope) e, da eleição de presidente, aptos, comparecimento e votos."""
    env = filhos(filhos(b)[0][3])
    ident = next(v for c, n, k, v in env if c == 2 and n == 0 and k)
    local, secao = [inteiro(v) for c, n, k, v in filhos(ident) if not k]
    interno = next(v for c, n, k, v in env if c == 0 and n == 4)

    def achar(b):
        """Procura a sequência que começa com o código da eleição."""
        for c, n, k, v in filhos(b):
            if k:
                f = filhos(v)
                if len(f) >= 3 and not f[0][2] and f[0][1] == 2 and inteiro(f[0][3]) == eleicao:
                    return f
                r = achar(v)
                if r:
                    return r
        return None

    f = achar(interno)
    out = {"local": local, "secao": secao, "aptos": inteiro(f[1][3]), "brancos": 0, "nulos": 0, "outros": 0}
    out.update({k: 0 for k in NUM.values()})
    resultados = next(v for c, n, k, v in f if k)
    cargo = filhos(filhos(resultados)[0][3])  # [tipo de cargo, comparecimento, votos]
    out["comparecimento"] = inteiro(cargo[1][3])
    votos = filhos(filhos(cargo[2][3])[0][3])
    lista = next(v for c, n, k, v in votos if k)
    for _, _, _, voto in filhos(lista):
        campos = {(c, n): v for c, n, k, v in filhos(voto)}
        tipo, qtd = inteiro(campos[2, 1]), inteiro(campos[2, 2])
        if tipo == 1:
            codigo = inteiro(filhos(campos[2, 3])[1][3])
            out[NUM.get(codigo, "outros")] += qtd
        elif tipo == 2:
            out["brancos"] += qtd
        elif tipo == 3:
            out["nulos"] += qtd
    return out


def secoes(uf, mun, pleito):
    arq = TSE / "bu" / pleito / f"{uf}-cs.json"
    if not arq.exists():
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_bytes(baixar(URNA.format(p=pleito) + f"config/{uf}/{uf}-p{int(pleito):06d}-cs.json"))
    cfg = json.loads(arq.read_text(encoding="utf-8"))
    m = next(m for m in cfg["abr"][0]["mu"] if m["cd"] == mun)
    return [(z["cd"], s["ns"]) for z in m["zon"] for s in z["sec"]]


def bu(uf, mun, pleito, zona, sec):
    """Baixa (se ainda não tem) o boletim de uma seção. Devolve os bytes ou None."""
    arq = TSE / "bu" / pleito / f"{uf}{mun}" / f"z{zona}s{sec}.bu"
    if arq.exists() and arq.stat().st_size:
        return arq.read_bytes()
    base = URNA.format(p=pleito) + f"dados/{uf}/{mun}/{zona}/{sec}/"
    try:
        aux = json.loads(baixar(base + f"p{int(pleito):06d}-{uf}-m{mun}-z{zona}-s{sec}-aux.json"))
        h = aux["hashes"][-1]
        nome = next(a["nm"] for a in h["arq"] if a["tp"] == "bu")
        b = baixar(base + f"{h['hash']}/{nome}")
    except Exception:
        return None
    arq.parent.mkdir(parents=True, exist_ok=True)
    arq.write_bytes(b)
    return b


def locais(uf, mun):
    """(turno, zona, seção) -> local de votação, endereço, bairro, latitude e longitude."""
    zp = TSE / "locais" / "eleitorado_local_votacao_2026.zip"
    out = {}
    with zipfile.ZipFile(zp) as z:
        with z.open(f"eleitorado_local_votacao_2026_{uf.upper()}.csv") as fh:
            for r in csv.DictReader(io.TextIOWrapper(fh, encoding="latin-1"), delimiter=";"):
                if r["CD_MUNICIPIO"] == mun:
                    out[int(r["NR_TURNO"]), int(r["NR_ZONA"]), int(r["NR_SECAO"])] = {
                        "local_votacao": r["NM_LOCAL_VOTACAO"].title(), "bairro": " ".join(r["NM_BAIRRO"].split()).title(),
                        "lat": r["NR_LATITUDE"].replace(",", "."), "lon": r["NR_LONGITUDE"].replace(",", ".")}
    return out


def main():
    uf, mun, nome = (sys.argv[1:4] if len(sys.argv) >= 4 else ("pr", "75353", "curitiba"))
    loc = locais(uf, mun)
    por_secao = {}
    for turno, (pleito, eleicao) in PLEITOS.items():
        lista = secoes(uf, mun, pleito)
        with ThreadPoolExecutor(max_workers=8) as ex:
            dados = list(ex.map(lambda zs: (zs, bu(uf, mun, pleito, *zs)), lista))
        falta = 0
        for (zona, sec), b in dados:
            if b is None:
                falta += 1
                continue
            x = ler_bu(b, eleicao)
            por_secao.setdefault((int(zona), int(sec)), {})[turno] = x
        print(f"{turno}º turno: {len(lista) - falta} de {len(lista)} boletins lidos")

    campos = ["aptos", "comparecimento", "lula", "flavio", "brancos", "nulos"]
    campos_1t = campos + ["cury", "renan", "caiado", "outros"]
    linhas = []
    for (zona, sec), t in sorted(por_secao.items()):
        if 1 not in t or 2 not in t:
            continue
        lv = loc.get((2, zona, sec)) or loc.get((1, zona, sec)) or {"local_votacao": "", "bairro": "(sem local)", "lat": "", "lon": ""}
        linha = {"zona": zona, "secao": sec, **lv}
        linha.update({f"{k}_1t": t[1][k] for k in campos_1t})
        linha.update({f"{k}_2t": t[2][k] for k in campos})
        linhas.append(linha)
    with (PASTA / f"{nome}_secoes.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)

    somas = {}
    for l in linhas:
        s = somas.setdefault(l["bairro"], {"bairro": l["bairro"], "secoes": 0})
        s["secoes"] += 1
        for k in [f"{c}_1t" for c in campos_1t] + [f"{c}_2t" for c in campos]:
            s[k] = s.get(k, 0) + l[k]
    for s in somas.values():
        for t in ("1t", "2t"):
            s[f"abstencao_{t}"] = s[f"aptos_{t}"] - s[f"comparecimento_{t}"]
            lf = s[f"lula_{t}"] + s[f"flavio_{t}"]
            s[f"pct_lula_{t}"] = round(s[f"lula_{t}"] / lf * 100, 2) if lf else None
            s[f"pct_abstencao_{t}"] = round(s[f"abstencao_{t}"] / s[f"aptos_{t}"] * 100, 2) if s[f"aptos_{t}"] else None
    with (PASTA / f"{nome}_bairros.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(next(iter(somas.values()))))
        w.writeheader()
        w.writerows(sorted(somas.values(), key=lambda s: -s["aptos_2t"]))
    tot = {k: sum(l[k] for l in linhas) for k in linhas[0] if k.endswith(("_1t", "_2t"))}
    print(f"{len(linhas)} seções nos dois turnos, {len(somas)} bairros · aptos {tot['aptos_2t']:,} ·"
          f" Lula {tot['lula_1t']:,} → {tot['lula_2t']:,} · Flávio {tot['flavio_1t']:,} → {tot['flavio_2t']:,}".replace(",", "."))
    print(f"Gravado em dados/{nome}_secoes.csv e dados/{nome}_bairros.csv\n")
    relatorio(list(somas.values()), linhas)


def relatorio(bairros, secoes):
    """Os bairros e os locais de votação que mais mudaram, em % e em pessoas."""
    mil = lambda n: f"{n:+,.0f}".replace(",", ".") if n else "0"
    for b in bairros:
        b["d_lula"], b["d_flavio"] = b["lula_2t"] - b["lula_1t"], b["flavio_2t"] - b["flavio_1t"]
        b["swing"] = b["pct_lula_2t"] - b["pct_lula_1t"]
        b["d_abst"] = b["abstencao_2t"] - b["abstencao_1t"]
        b["d_bn"] = b["brancos_2t"] + b["nulos_2t"] - b["brancos_1t"] - b["nulos_1t"]
        b["outros"] = b["cury_1t"] + b["renan_1t"] + b["caiado_1t"] + b["outros_1t"]
    grandes = [b for b in bairros if b["aptos_2t"] >= 5000]

    def linha(b):
        return (f"  {b['bairro'][:22]:22} Lula {b['pct_lula_1t']:5.1f}% → {b['pct_lula_2t']:5.1f}% ({b['swing']:+.1f})"
                f"  votos Lula {mil(b['d_lula']):>7} · Flávio {mil(b['d_flavio']):>7}"
                f"  · abstenção {mil(b['d_abst']):>7} · brancos+nulos {mil(b['d_bn']):>6}  ({b['aptos_2t']:,} eleitores)".replace(",", "."))

    for titulo, chave, rev in (("Onde o Lula tem mais %", "pct_lula_2t", True), ("Onde o Flávio tem mais %", "pct_lula_2t", False),
                               ("Onde o Lula mais cresceu (pontos, 1º → 2º turno)", "swing", True),
                               ("Onde o Lula menos cresceu", "swing", False),
                               ("Onde o Lula ganhou mais votos (pessoas)", "d_lula", True),
                               ("Onde o Flávio ganhou mais votos (pessoas)", "d_flavio", True),
                               ("Onde a abstenção mais caiu (pessoas)", "d_abst", False)):
        print(titulo + " · bairros com 5 mil eleitores ou mais")
        for b in sorted(grandes, key=lambda b: b[chave], reverse=rev)[:5]:
            print(linha(b))
        print()
    lula = [b for b in bairros if b["pct_lula_2t"] and b["pct_lula_2t"] > 50]
    print(f"Bairros com o Lula na frente no 2º turno: {len(lula)} de {len(bairros)}"
          + (f" ({', '.join(b['bairro'] for b in lula)})" if lula else ""))

    # locais de votação (escolas): somando as seções de cada local
    locais = {}
    for s in secoes:
        l = locais.setdefault((s["local_votacao"], s["bairro"]), {"l1": 0, "f1": 0, "l2": 0, "f2": 0, "aptos": 0})
        for a, b in (("l1", "lula_1t"), ("f1", "flavio_1t"), ("l2", "lula_2t"), ("f2", "flavio_2t"), ("aptos", "aptos_2t")):
            l[a] += s[b]
    locais = [(k, v, v["l2"] / (v["l2"] + v["f2"]) * 100, v["l1"] / (v["l1"] + v["f1"]) * 100)
              for k, v in locais.items() if v["aptos"] >= 1000 and v["l2"] + v["f2"] and v["l1"] + v["f1"]]
    print("\nLocais de votação (escolas) com mil eleitores ou mais: os extremos")
    for titulo, lista in (("mais Lula", sorted(locais, key=lambda x: -x[2])[:4]), ("mais Flávio", sorted(locais, key=lambda x: x[2])[:4]),
                          ("o Lula mais cresceu", sorted(locais, key=lambda x: -(x[2] - x[3]))[:4])):
        print(f"  {titulo}:")
        for (nome, bairro), v, p2, p1 in lista:
            print(f"    {nome[:44]:44} {bairro[:18]:18} Lula {p1:5.1f}% → {p2:5.1f}%  ({v['l2']:,} x {v['f2']:,})".replace(",", "."))


if __name__ == "__main__":
    main()
