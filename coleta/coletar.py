#!/usr/bin/env python3
"""Coleta automática da apuração direto do TSE (resultados.tse.jus.br).

Cada coleta:
  - salva os JSON brutos em dados/brutos/<horário>/ (para auditoria)
  - adiciona o placar nacional em dados/snapshots.csv
  - adiciona o andamento de cada UF em dados/estados.csv
  - adiciona todos os candidatos em dados/candidatos.csv
  - baixa a curva de evolução do UOL (2026 e 2022), regenera painel.html e atualiza dados/apuracao.sqlite
  - opcionalmente tira prints recortados do UOL e do g1 (--print, via prints.js)

Uso:
  python3 coleta/coletar.py                 # uma coleta
  python3 coleta/coletar.py --a-cada 180    # repete a cada 180 s até Ctrl+C
  python3 coleta/coletar.py --a-cada 180 --print
"""
import argparse
import csv
import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

# 6257 = Presidente 1º turno; 6258 = Presidente 2º turno (ver resultados.tse.jus.br/oficial/comum/config/ele-c.json)
CODIGO = "6258"
BASE = f"https://resultados.tse.jus.br/oficial/ele2026/{CODIGO}/dados"
ELEICAO = CODIGO.zfill(6)
UFS = ["br", "ac", "al", "am", "ap", "ba", "ce", "df", "es", "go", "ma", "mg", "ms", "mt",
       "pa", "pb", "pe", "pi", "pr", "rj", "rn", "ro", "rr", "rs", "sc", "se", "sp", "to", "zz"]
UOL_EV_2026 = "https://stc.eleicoes2026.uol.com/2026/2turno/br/br-c1-ev.json"
UOL_EV_2022 = "https://stc.eleicoes2026.uol.com/2026/historical/2022/br-c1-t2-ev.json"

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "dados"
SNAPSHOTS = PASTA / "snapshots.csv"
ESTADOS = PASTA / "estados.csv"
CANDIDATOS = PASTA / "candidatos.csv"
ULTIMA = PASTA / ".ultima_coleta_tse"


def f(s):
    return float(s.replace(",", "."))


def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def anexar(arquivo, colunas, linhas):
    novo = not arquivo.exists()
    with arquivo.open("a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if novo:
            w.writerow(colunas)
        w.writerows(linhas)


def candidatos(dados_u):
    out = []
    for agr in dados_u["carg"][0]["agr"]:
        for par in agr["par"]:
            for c in par["cand"]:
                out.append({"nome": c["nmu"], "numero": c["n"], "votos": int(c["vap"]), "pct": f(c["pvapn"])})
    return sorted(out, key=lambda c: -c["votos"])


def tirar_prints(pasta):
    """Prints recortados (placar/evolução/estados/regiões do UOL e mapa do g1) via prints.js."""
    try:
        r = subprocess.run(["node", str(Path(__file__).resolve().parent / "prints.js"), str(pasta)],
                           timeout=150, capture_output=True, text=True)
        return len(list(pasta.glob("*.png")))
    except Exception:
        return 0


def baixar_uol():
    """Curvas de evolução do UOL: 2026 (desde o início da apuração) e histórico 2022."""
    for nome, url in [("uol-evolucao-2026.json", UOL_EV_2026), ("uol-historico-2022.json", UOL_EV_2022)]:
        if nome.endswith("2022.json") and (PASTA / nome).exists():
            continue  # histórico não muda
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://noticias.uol.com.br/"})
            with urllib.request.urlopen(req, timeout=20) as r:
                (PASTA / nome).write_bytes(r.read())
        except Exception as e:
            print(f"  ! UOL {nome}: {e}")


def gerar_painel():
    for script in ("painel/painel.py", "analise/banco.py", "analise/exportar.py", "analise/perguntas.py"):  # painel, banco, exportação, perguntas
        try:
            subprocess.run([sys.executable, str(RAIZ / script)], timeout=60, capture_output=True)
        except Exception as e:
            print(f"  ! {script}: {e}")


def coletar(com_print=False):
    agora = datetime.now()
    horario = agora.strftime("%Y-%m-%d %H:%M")

    ab = baixar(f"{BASE}/br/br-e{ELEICAO}-ab.json")
    # baixa tudo antes de decidir: os arquivos dos estados andam na frente do nacional
    arquivos = {}
    for uf in UFS:
        try:
            arquivos[uf] = baixar(f"{BASE}/{uf}/{uf}-c0001-e{ELEICAO}-u.json")
        except Exception as e:
            print(f"  ! falha em {uf}: {e}")
    u_br = arquivos["br"]
    versao_tse = f"{u_br['dg']} {u_br['hg']}"
    assinatura = "|".join(f"{uf}:{u['dg']} {u['hg']}" for uf, u in sorted(arquivos.items()))
    if ULTIMA.exists() and ULTIMA.read_text().strip() == assinatura:
        print(f"{horario} | TSE sem atualização (nacional {versao_tse}), nada gravado")
        return {"gravou": False, "urnas": None, "tf": u_br.get("tf"), "md": u_br.get("md")}

    pasta_bruta = PASTA / "brutos" / agora.strftime("%Y%m%d-%H%M%S")
    pasta_bruta.mkdir(parents=True, exist_ok=True)
    (pasta_bruta / "br-ab.json").write_text(json.dumps(ab, ensure_ascii=False), encoding="utf-8")

    linhas_estados, linhas_cand = [], []
    nacional = None

    for uf in UFS:
        u = arquivos.get(uf)
        if not u:
            continue
        (pasta_bruta / f"{uf}-u.json").write_text(json.dumps(u, ensure_ascii=False), encoding="utf-8")
        cands = candidatos(u)
        por_num = {c["numero"]: c for c in cands}
        flavio, lula = por_num.get("22"), por_num.get("13")
        # % de seções do PRÓPRIO arquivo de votos: o -ab.json fica minutos à frente dos votos
        urnas = f(u["s"]["pstn"])
        eleitorado = int(u["e"]["te"])

        for c in cands:
            linhas_cand.append([horario, uf.upper(), c["numero"], c["nome"], c["votos"], c["pct"]])

        if uf == "br":
            nacional = (urnas, lula, flavio)
        else:
            linhas_estados.append([horario, uf.upper(), urnas, eleitorado,
                                   flavio["pct"] if flavio else "", lula["pct"] if lula else "", "tse"])

    # nacional = soma das UFs + exterior (o arquivo nacional do TSE às vezes atrasa em relação aos estados)
    ufs_u = [u for uf, u in arquivos.items() if uf != "br"]
    if len(ufs_u) == len(UFS) - 1:
        vv = sum(int(u["v"]["vv"]) for u in ufs_u)
        soma = {}
        for u in ufs_u:
            for c in candidatos(u):
                soma[c["numero"]] = soma.get(c["numero"], 0) + c["votos"]
        urnas = sum(int(u["s"]["st"]) for u in ufs_u) / sum(int(u["s"]["ts"]) for u in ufs_u) * 100
        flavio = {"votos": soma["22"], "pct": soma["22"] / vv * 100}
        lula = {"votos": soma["13"], "pct": soma["13"] / vv * 100}
    else:
        urnas, lula, flavio = nacional
    anexar(SNAPSHOTS, ["horario", "urnas_pct", "lula_pct", "flavio_pct", "lula_votos", "flavio_votos", "nota"],
           [[horario, round(urnas, 2), round(lula["pct"], 2), round(flavio["pct"], 2),
             lula["votos"], flavio["votos"], f"TSE {versao_tse} (soma UFs)"]])
    anexar(ESTADOS, ["horario", "uf", "urnas_pct", "eleitorado", "flavio_pct", "lula_pct", "fonte"], linhas_estados)
    anexar(CANDIDATOS, ["horario", "abrangencia", "numero", "candidato", "votos", "pct"], linhas_cand)
    ULTIMA.write_text(assinatura)

    msg = f"✔ {horario} | {urnas:.2f}% urnas | Flávio {flavio['pct']:.2f}% x Lula {lula['pct']:.2f}% | TSE {versao_tse}"
    baixar_uol()
    gerar_painel()
    msg += " | painel ok"
    if com_print:
        n = tirar_prints(pasta_bruta)
        msg += f" | {n} prints"
    print(msg, flush=True)
    return {"gravou": True, "urnas": urnas, "tf": u_br.get("tf"), "md": u_br.get("md"), "horario": horario}


def git_enviar(mensagem):
    """Commita e envia os dados ao GitHub (dados/ e site/dados.js). Silencioso se não houver mudança."""
    raiz = str(RAIZ)
    try:
        subprocess.run(["git", "-C", raiz, "add", "-A", "dados/", "site/dados.js"], capture_output=True, timeout=60)
        r = subprocess.run(["git", "-C", raiz, "commit", "-q", "-m", mensagem, "-m",
                            "Commit automático do coletor (coleta/coletar.py --git)."],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            return "nada a commitar"
        r = subprocess.run(["git", "-C", raiz, "push", "-q"], capture_output=True, text=True, timeout=120)
        return "enviado" if r.returncode == 0 else f"push falhou: {r.stderr.strip()[:120]}"
    except Exception as e:
        return f"git falhou: {e}"


def main():
    p = argparse.ArgumentParser(description="Coleta a apuração direto do TSE")
    p.add_argument("--a-cada", type=int, default=0, help="segundos entre coletas (0 = só uma)")
    p.add_argument("--print", action="store_true", help="salva print da página do g1 em cada coleta")
    p.add_argument("--eleicao", default=CODIGO, help="código TSE da eleição (6257 = 1º turno, 6258 = 2º turno)")
    p.add_argument("--git", action="store_true", help="commita e envia os dados ao GitHub a cada 30 min e no fim")
    p.add_argument("--parar-no-fim", action="store_true",
                   help="encerra quando o TSE finalizar a totalização (tf = s) ou após 1 h sem novidade com ≥ 99,9%%")
    a = p.parse_args()
    global BASE, ELEICAO
    BASE = f"https://resultados.tse.jus.br/oficial/ele2026/{a.eleicao}/dados"
    ELEICAO = a.eleicao.zfill(6)
    ultimo_dado = ultimo_commit = time.time()
    urnas = 0.0
    pendente = False
    while True:
        r = None
        try:
            r = coletar(a.print)
        except Exception as e:
            print(f"{datetime.now():%H:%M} | erro na coleta: {e}", flush=True)
        if r and r["gravou"]:
            ultimo_dado, urnas, pendente = time.time(), r["urnas"], True
        if a.git and pendente and time.time() - ultimo_commit >= 1800:
            print(f"{datetime.now():%H:%M} | git: {git_enviar(f'Dados: coleta automática até {datetime.now():%H:%M} ({urnas:.2f}% apurado)')}", flush=True)
            ultimo_commit, pendente = time.time(), False
        fim = r is not None and (r.get("tf") == "s" or (urnas >= 99.9 and time.time() - ultimo_dado >= 3600))
        if fim and a.parar_no_fim:
            if a.git:
                print(f"{datetime.now():%H:%M} | git: {git_enviar(f'Dados: apuração encerrada ({urnas:.2f}% apurado)')}", flush=True)
            print(f"{datetime.now():%H:%M} | fim da apuração detectado (tf={r.get('tf')}, {urnas:.2f}%), coletor encerrado", flush=True)
            break
        if not a.a_cada:
            break
        time.sleep(a.a_cada)


if __name__ == "__main__":
    main()
