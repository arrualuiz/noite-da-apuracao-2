#!/usr/bin/env python3
"""Monta o banco SQLite dados/apuracao.sqlite a partir dos JSON brutos do TSE.

Incremental: só insere coletas que ainda não estão no banco.
Uso: python3 analise/banco.py            (o coletar.py chama a cada coleta)
     python3 analise/banco.py --recriar  (apaga e reconstrói do zero)

Tabelas (formato "longo", pronto para R/dplyr/ggplot):
  coletas     uma linha por coleta (coleta_id, horario, versão do arquivo nacional)
  ufs         UF, nome, região
  candidatos  número, nome, partido
  apuracao    coleta × abrangência (BR oficial, cada UF, ZZ): seções, eleitorado, votos totais, válidos, brancos, nulos
  votos       coleta × abrangência × candidato: votos e % dos válidos
Views:
  v_votos           votos com horário, região e nome do candidato
  v_nacional_soma   nacional calculado pela soma das UFs (mais atual que o arquivo BR)
"""
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BRUTOS = RAIZ / "dados" / "brutos"
BANCO = RAIZ / "dados" / "apuracao.sqlite"

NOMES = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão", "MG": "Minas Gerais",
    "MS": "Mato Grosso do Sul", "MT": "Mato Grosso", "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco",
    "PI": "Piauí", "PR": "Paraná", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RO": "Rondônia",
    "RR": "Roraima", "RS": "Rio Grande do Sul", "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo",
    "TO": "Tocantins", "ZZ": "Exterior",
}
REGIOES = {
    "Norte": ["AC", "AM", "AP", "PA", "RO", "RR", "TO"],
    "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Centro-Oeste": ["DF", "GO", "MS", "MT"],
    "Sudeste": ["ES", "MG", "RJ", "SP"],
    "Sul": ["PR", "RS", "SC"],
    "Exterior": ["ZZ"],
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS coletas (
  coleta_id TEXT PRIMARY KEY,          -- AAAAMMDD-HHMMSS (nome da pasta bruta)
  horario TEXT NOT NULL,               -- 'AAAA-MM-DD HH:MM:SS' (hora local da coleta)
  versao_tse_br TEXT                   -- data/hora de geração do arquivo nacional do TSE
);
CREATE TABLE IF NOT EXISTS ufs (
  uf TEXT PRIMARY KEY, nome TEXT, regiao TEXT
);
CREATE TABLE IF NOT EXISTS candidatos (
  numero INTEGER PRIMARY KEY, nome TEXT, partido TEXT
);
CREATE TABLE IF NOT EXISTS apuracao (
  coleta_id TEXT REFERENCES coletas, abrangencia TEXT,   -- 'BR' ou UF
  versao_tse TEXT,
  secoes_total INTEGER, secoes_apuradas INTEGER, secoes_pct REAL,
  eleitorado INTEGER, eleitorado_apurado INTEGER,
  comparecimento INTEGER, abstencao INTEGER,
  votos_total INTEGER, validos INTEGER, brancos INTEGER, nulos INTEGER,
  PRIMARY KEY (coleta_id, abrangencia)
);
CREATE TABLE IF NOT EXISTS votos (
  coleta_id TEXT REFERENCES coletas, abrangencia TEXT, numero INTEGER REFERENCES candidatos,
  votos INTEGER, pct_validos REAL,
  PRIMARY KEY (coleta_id, abrangencia, numero)
);
DROP VIEW IF EXISTS v_votos;
CREATE VIEW v_votos AS
  SELECT c.horario, v.coleta_id, v.abrangencia, u.nome AS nome_uf, u.regiao,
         v.numero, k.nome AS candidato, k.partido, v.votos, v.pct_validos
  FROM votos v JOIN coletas c USING (coleta_id)
  JOIN candidatos k USING (numero)
  LEFT JOIN ufs u ON u.uf = v.abrangencia;
DROP VIEW IF EXISTS v_nacional_soma;
CREATE VIEW v_nacional_soma AS
  SELECT c.horario, v.coleta_id, v.numero, k.nome AS candidato,
         SUM(v.votos) AS votos,
         100.0 * SUM(v.votos) / (SELECT SUM(a.validos) FROM apuracao a
                                 WHERE a.coleta_id = v.coleta_id AND a.abrangencia <> 'BR') AS pct_validos
  FROM votos v JOIN coletas c USING (coleta_id) JOIN candidatos k USING (numero)
  WHERE v.abrangencia <> 'BR'
  GROUP BY v.coleta_id, v.numero;
"""


def f(s):
    return float(str(s).replace(",", "."))


def main():
    if "--recriar" in sys.argv and BANCO.exists():
        BANCO.unlink()
    con = sqlite3.connect(BANCO)
    con.executescript(SCHEMA)
    con.executemany("INSERT OR IGNORE INTO ufs VALUES (?,?,?)",
                    [(uf, NOMES[uf], r) for r, lista in REGIOES.items() for uf in lista])
    ja = {r[0] for r in con.execute("SELECT coleta_id FROM coletas")}
    novas = 0
    for pasta in sorted(p for p in BRUTOS.iterdir() if p.is_dir()):
        if pasta.name in ja or not (pasta / "br-u.json").exists():
            continue
        arquivos = {}
        for uf in ["BR", *NOMES]:
            arq = pasta / f"{uf.lower()}-u.json"
            if arq.exists():
                arquivos[uf] = json.loads(arq.read_text(encoding="utf-8"))
        if len(arquivos) < len(NOMES) + 1:
            continue  # coleta incompleta: fica de fora
        br = arquivos["BR"]
        horario = datetime.strptime(pasta.name, "%Y%m%d-%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
        con.execute("INSERT INTO coletas VALUES (?,?,?)", (pasta.name, horario, f"{br['dg']} {br['hg']}"))
        for ab, u in arquivos.items():
            s, e, v = u["s"], u["e"], u["v"]
            con.execute("INSERT INTO apuracao VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                pasta.name, ab, f"{u['dg']} {u['hg']}",
                int(s["ts"]), int(s["st"]), f(s["pstn"]),
                int(e["te"]), int(e["est"]), int(e["c"]), int(e["a"]),
                int(v["tv"]), int(v["vv"]), int(v["vb"]), int(v["tvn"])))
            for agr in u["carg"][0]["agr"]:
                for par in agr["par"]:
                    for c in par["cand"]:
                        con.execute("INSERT OR IGNORE INTO candidatos VALUES (?,?,?)",
                                    (int(c["n"]), c["nmu"].title(), par["sg"]))
                        con.execute("INSERT INTO votos VALUES (?,?,?,?,?)",
                                    (pasta.name, ab, int(c["n"]), int(c["vap"]), f(c["pvapn"])))
        novas += 1
    con.commit()
    total = con.execute("SELECT COUNT(*) FROM coletas").fetchone()[0]
    linhas = con.execute("SELECT COUNT(*) FROM votos").fetchone()[0]
    con.close()
    print(f"banco: +{novas} coletas novas · {total} coletas · {linhas} linhas de votos · {BANCO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
