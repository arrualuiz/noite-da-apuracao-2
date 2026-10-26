#!/usr/bin/env python3
"""Os números do TSE fecham? Checagens de consistência com os dados públicos da eleição.

1. Cada urna de Curitiba (boletim de urna, analise/bairros.py): votos de cada candidato + brancos + nulos
   = quem foi votar, e ninguém vota acima dos aptos. E a soma das 4.056 urnas = o total que o TSE divulgou.
2. Cada município do Brasil e do exterior (arquivos de resultado do TSE, analise/abstencao.py):
   comparecimento + abstenção = eleitorado das seções apuradas; válidos + brancos + nulos = comparecimento;
   Lula + Flávio = válidos; comparecimento nunca acima do eleitorado.
3. Soma de todos os municípios = o total do Brasil.

Isso mostra que os números são coerentes entre si e batem com os boletins de urna (que são impressos e
afixados em cada seção e podem ser conferidos por qualquer um). Não é uma auditoria do sistema inteiro.

Uso: python3 analise/auditoria.py
"""
import csv
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "dados"


def mil(n):
    return f"{n:,}".replace(",", ".")


def main():
    falhas = 0

    # 1. urnas de Curitiba
    S = list(csv.DictReader((PASTA / "curitiba_secoes.csv").open(encoding="utf-8")))
    i = lambda s, k: int(s[k])
    fecha2 = sum(i(s, "lula_2t") + i(s, "flavio_2t") + i(s, "brancos_2t") + i(s, "nulos_2t") == i(s, "comparecimento_2t") for s in S)
    fecha1 = sum(sum(i(s, f"{k}_1t") for k in ("lula", "flavio", "cury", "renan", "caiado", "outros", "brancos", "nulos")) == i(s, "comparecimento_1t") for s in S)
    acima = sum(i(s, "comparecimento_2t") > i(s, "aptos_2t") for s in S)
    pasta = max((d / "todos-mun" for d in (PASTA / "brutos").iterdir() if (d / "todos-mun").exists()), key=lambda p: p.parent.name)
    cwb = json.loads((pasta / "pr75353.json").read_text(encoding="utf-8"))
    oficial = {x["n"]: int(x["vap"]) for a in cwb["carg"][0]["agr"] for p in a["par"] for x in p["cand"]}
    soma = {"13": sum(i(s, "lula_2t") for s in S), "22": sum(i(s, "flavio_2t") for s in S)}
    print(f"1. CURITIBA, URNA POR URNA ({mil(len(S))} boletins de urna, nos dois turnos)")
    print(f"   votos dos candidatos + brancos + nulos = quem foi votar: {fecha1} no 1º turno e {fecha2} no 2º")
    print(f"   urnas com mais votantes que aptos: {acima}")
    print(f"   soma dos boletins: Lula {mil(soma['13'])} x Flávio {mil(soma['22'])} · TSE: Lula {mil(oficial['13'])} x Flávio {mil(oficial['22'])}"
          f" → {'iguais' if soma == {k: oficial[k] for k in soma} else 'DIFERENTES'}")
    falhas += (fecha1 != len(S)) + (fecha2 != len(S)) + acima + (soma != {k: oficial[k] for k in soma})

    # 2. municípios
    n = ok = 0
    nao_instaladas = []
    tot = {"c": 0, "a": 0, "vv": 0, "13": 0, "22": 0}
    for f in sorted(pasta.glob("*.json")):
        u = json.loads(f.read_text(encoding="utf-8"))
        e, v = u["e"], u["v"]
        te, est, esnt, c, a = (int(e[k]) for k in ("te", "est", "esnt", "c", "a"))
        vv, vb, vn = int(v["vv"]), int(v["vb"]), int(v["tvn"])
        cand = {x["n"]: int(x["vap"]) for g in u["carg"][0]["agr"] for p in g["par"] for x in p["cand"]}
        n += 1
        if c + a == est and est + esnt == te and vv + vb + vn == c and sum(cand.values()) == vv and c <= te:
            ok += 1
        elif c == a == 0 and int(e.get("esni", 0)) == te:  # nenhuma seção instalada (cidades pequenas do exterior)
            nao_instaladas.append((f.stem, te))
        else:
            print(f"   ! {f.stem}: {e}")
        tot["c"] += c
        tot["a"] += a
        tot["vv"] += vv
        tot["13"] += cand.get("13", 0)
        tot["22"] += cand.get("22", 0)
    falhas += n - ok - len(nao_instaladas)
    print(f"\n2. TODOS OS MUNICÍPIOS ({mil(n)} arquivos, Brasil e exterior, coleta de {pasta.parent.name[9:11]}:{pasta.parent.name[11:13]})")
    print(f"   fecham todas as contas: {mil(ok)}")
    print(f"   sem nenhuma seção instalada: {len(nao_instaladas)} (todas no exterior, {sum(t for _, t in nao_instaladas)} eleitores ao todo)")
    print(f"   com conta que não fecha: {n - ok - len(nao_instaladas)}")

    # 3. soma dos municípios x Brasil (na mesma coleta)
    br = json.loads((pasta.parent / "br-u.json").read_text(encoding="utf-8"))
    cb = {x["n"]: int(x["vap"]) for a in br["carg"][0]["agr"] for p in a["par"] for x in p["cand"]}
    iguais = tot["13"] == cb["13"] and tot["22"] == cb["22"] and tot["c"] == int(br["e"]["c"])
    print(f"\n3. SOMA DOS MUNICÍPIOS x TOTAL DO BRASIL (mesma coleta, {br['s']['pstn']}% apurado)")
    print(f"   soma: Lula {mil(tot['13'])} x Flávio {mil(tot['22'])}, {mil(tot['c'])} votantes")
    print(f"   TSE:  Lula {mil(cb['13'])} x Flávio {mil(cb['22'])}, {mil(int(br['e']['c']))} votantes → {'iguais' if iguais else 'DIFERENTES'}")
    falhas += not iguais
    print(f"\n{'Nenhuma inconsistência.' if not falhas else f'{falhas} inconsistências.'}")


if __name__ == "__main__":
    main()
