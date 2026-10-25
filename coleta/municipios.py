#!/usr/bin/env python3
"""Capital x Grande SP x interior (e Rio, BH), a cada coleta.

Baixa do TSE o resultado dos municípios da região metropolitana de São Paulo e das capitais
do RJ e de MG, guarda os JSON junto da última coleta (dados/brutos/<coleta>/mun/) e grava os
segmentos em dados/segmentos.csv. O "resto" de cada estado é o estado menos as cidades baixadas.

Na primeira vez, guarda também o resultado final do 1º turno desses municípios
(dados/historico/2026-t1-segmentos.csv), para comparar.

Uso: python3 coleta/municipios.py   (o coletar.py chama isto a cada coleta)
"""
import csv
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "dados"
BASE = "https://resultados.tse.jus.br/oficial/ele2026/{eleicao}"
CONFIG = PASTA / "municipios-6258.json"
SEGMENTOS = PASTA / "segmentos.csv"
HIST_1T = PASTA / "historico" / "2026-t1-segmentos.csv"

# Região metropolitana de São Paulo (39 municípios, com a capital), nomes como o TSE escreve
RMSP = ["ARUJÁ", "BARUERI", "BIRITIBA MIRIM", "CAIEIRAS", "CAJAMAR", "CARAPICUÍBA", "COTIA", "DIADEMA",
        "EMBU DAS ARTES", "EMBU-GUAÇU", "FERRAZ DE VASCONCELOS", "FRANCISCO MORATO", "FRANCO DA ROCHA",
        "GUARAREMA", "GUARULHOS", "ITAPECERICA DA SERRA", "ITAPEVI", "ITAQUAQUECETUBA", "JANDIRA", "JUQUITIBA",
        "MAIRIPORÃ", "MAUÁ", "MOGI DAS CRUZES", "OSASCO", "PIRAPORA DO BOM JESUS", "POÁ", "RIBEIRÃO PIRES",
        "RIO GRANDE DA SERRA", "SALESÓPOLIS", "SANTA ISABEL", "SANTANA DE PARNAÍBA", "SANTO ANDRÉ",
        "SÃO BERNARDO DO CAMPO", "SÃO CAETANO DO SUL", "SÃO LOURENÇO DA SERRA", "SÃO PAULO", "SUZANO",
        "TABOÃO DA SERRA", "VARGEM GRANDE PAULISTA"]
COLUNAS = ["horario", "coleta_id", "segmento", "eleitorado", "apurado_eleit", "lula", "flavio", "comparecimento", "abstencao"]


def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def municipios():
    """{uf: {segmento: [códigos TSE]}}: capital de SP, RJ e MG e o resto da Grande SP."""
    if not CONFIG.exists():
        CONFIG.write_bytes(baixar(f"{BASE.format(eleicao='6258')}/config/mun-e006258-cm.json"))
    abr = {a["cd"]: a["mu"] for a in json.loads(CONFIG.read_text(encoding="utf-8"))["abr"]}
    capital = {uf: [m["cd"] for m in abr[uf] if m.get("c") == "s"] for uf in ("sp", "rj", "mg")}
    grande_sp = [m["cd"] for m in abr["sp"] if m["nm"] in RMSP and m.get("c") != "s"]
    faltando = set(RMSP) - {m["nm"] for m in abr["sp"]}
    if faltando:
        print(f"  ! municípios da Grande SP sem par no TSE: {sorted(faltando)}")
    return {"sp": {"SP capital": capital["sp"], "Grande SP (sem a capital)": grande_sp},
            "rj": {"Rio (capital)": capital["rj"]}, "mg": {"BH (capital)": capital["mg"]}}


def numeros(u):
    c = {x["n"]: int(x["vap"]) for a in u["carg"][0]["agr"] for p in a["par"] for x in p["cand"]}
    e = u["e"]
    return {"eleitorado": int(e["te"]), "apurado_eleit": int(e["est"]), "lula": c.get("13", 0),
            "flavio": c.get("22", 0), "comparecimento": int(e["c"]), "abstencao": int(e["a"])}


def somar(lista):
    return {k: sum(x[k] for x in lista) for k in COLUNAS[3:]}


def segmentos(ler_mun, ler_uf, mapa):
    """Soma os municípios de cada segmento e calcula o resto do estado."""
    out = {}
    for uf, segs in mapa.items():
        usados = []
        for nome, cods in segs.items():
            xs = [ler_mun(uf, cd) for cd in cods]
            out[nome] = somar(xs)
            usados += xs
        estado, soma = ler_uf(uf), somar(usados)
        resto = {k: estado[k] - soma[k] for k in estado}
        out[{"sp": "SP interior e litoral", "rj": "RJ sem a capital", "mg": "MG sem BH"}[uf]] = resto
    return out


def guardar_1t(mapa):
    """Resultado final do 1º turno de cada segmento (só Lula e Flávio)."""
    base = BASE.format(eleicao="6257")
    cache = {}

    def ler_mun(uf, cd):
        return numeros(json.loads(baixar(f"{base}/dados/{uf}/{uf}{cd}-c0001-e006257-u.json")))

    def ler_uf(uf):
        return numeros(json.loads(baixar(f"{base}/dados/{uf}/{uf}-c0001-e006257-u.json")))

    for nome, s in segmentos(ler_mun, ler_uf, mapa).items():
        cache[nome] = s
    with HIST_1T.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["segmento"] + COLUNAS[3:])
        for nome, s in cache.items():
            w.writerow([nome] + [s[k] for k in COLUNAS[3:]])


def main():
    mapa = municipios()
    if not HIST_1T.exists():
        guardar_1t(mapa)
    coletas = sorted(d for d in (PASTA / "brutos").iterdir() if (d / "br-u.json").exists())
    pasta = coletas[-1]
    if SEGMENTOS.exists() and pasta.name in SEGMENTOS.read_text(encoding="utf-8"):
        return  # esta coleta já foi feita
    destino = pasta / "mun"
    destino.mkdir(exist_ok=True)
    base = BASE.format(eleicao="6258")
    pedidos = [(uf, cd) for uf, segs in mapa.items() for cods in segs.values() for cd in cods]

    def baixar_mun(p):
        uf, cd = p
        arq = destino / f"{uf}{cd}-u.json"
        arq.write_bytes(baixar(f"{base}/dados/{uf}/{uf}{cd}-c0001-e006258-u.json"))

    with ThreadPoolExecutor(max_workers=6) as ex:
        list(ex.map(baixar_mun, pedidos))

    def ler_mun(uf, cd):
        return numeros(json.loads((destino / f"{uf}{cd}-u.json").read_text(encoding="utf-8")))

    def ler_uf(uf):
        return numeros(json.loads((pasta / f"{uf}-u.json").read_text(encoding="utf-8")))

    segs = segmentos(ler_mun, ler_uf, mapa)
    horario = f"{pasta.name[:4]}-{pasta.name[4:6]}-{pasta.name[6:8]} {pasta.name[9:11]}:{pasta.name[11:13]}:{pasta.name[13:15]}"
    novo = not SEGMENTOS.exists()
    with SEGMENTOS.open("a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if novo:
            w.writerow(COLUNAS)
        for nome, s in segs.items():
            w.writerow([horario, pasta.name, nome] + [s[k] for k in COLUNAS[3:]])
    print(f"municípios: {len(pedidos)} arquivos, {len(segs)} segmentos")


if __name__ == "__main__":
    main()
