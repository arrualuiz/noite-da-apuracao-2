#!/usr/bin/env python3
"""Mostra se a coleta automática está saudável.

Uso: python3 coleta/status.py
"""
import csv
import os
from datetime import datetime
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent / "dados"


def main():
    # processo
    pid_arq = PASTA / "coleta.pid"
    pid = pid_arq.read_text().strip() if pid_arq.exists() else None
    vivo = bool(pid) and Path(f"/proc/{pid}").exists()
    print(f"Coletor: {'RODANDO' if vivo else 'PARADO'} (PID {pid or '?'})")

    # última atividade no log
    log = PASTA / "coleta.log"
    if log.exists():
        idade = (datetime.now() - datetime.fromtimestamp(log.stat().st_mtime)).total_seconds() / 60
        print(f"Última linha no log: há {idade:.0f} min" + ("  ⚠ parado há muito tempo?" if idade > 8 else ""))
        erros = [l for l in log.read_text(encoding="utf-8").splitlines() if "erro" in l or "! " in l]
        print(f"Linhas de erro no log: {len(erros)}" + (f" (última: {erros[-1].strip()})" if erros else ""))

    # coletas gravadas: intervalo entre elas e se cada pasta está completa
    snaps = [r for r in csv.DictReader(open(PASTA / "snapshots.csv", encoding="utf-8")) if r["nota"].startswith("TSE")]
    brutos = sorted(d for d in (PASTA / "brutos").iterdir() if d.is_dir())
    print(f"\n{'coleta':<7} {'intervalo':>9} {'urnas':>7} {'Flávio':>7} {'Lula':>7} {'json':>5} {'prints':>6}  versão TSE")
    ant = None
    for r, d in zip(snaps, brutos):
        h = datetime.strptime(r["horario"], "%Y-%m-%d %H:%M")
        gap = f"{(h - ant).total_seconds() / 60:.0f} min" if ant else ""
        njson = len(list(d.glob("*.json")))
        npng = len(list(d.glob("*.png")))
        ok = "" if njson == 30 else "  ⚠ incompleta"
        print(f"{r['horario'][11:]:<7} {gap:>9} {float(r['urnas_pct']):>6.2f}% {float(r['flavio_pct']):>6.2f}% "
              f"{float(r['lula_pct']):>6.2f}% {njson:>5} {npng:>6}  {r['nota'][4:]}{ok}")
        ant = h
    if len(snaps) != len(brutos):
        print(f"⚠ {len(snaps)} linhas no CSV x {len(brutos)} pastas brutas")


if __name__ == "__main__":
    main()
