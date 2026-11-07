#!/usr/bin/env python3
"""jardineiro — passa toda semana pelos FALHAS/LESSONS/LICOES de todos os projetos e acha a erva que volta.

Uso:
  python3 jardineiro.py [--raiz ~/projetos] [--top 15] [--saida jardim/AAAA-MM-DD.md] [--sil PROJETO]
- Mede a reincidência: % dos registros que pertencem a um grupo de 2+ (o mesmo erro de novo).
- Lista os grupos que atravessam projetos (o erro mudou de casa, não sumiu).
- Ranking dos candidatos a subir de degrau (degrau.py, só que em todos os projetos).
- --sil: registra os 5 primeiros como ocorrência + proposta no SIL Loop R desse projeto (nunca adota sozinho).
Só lê arquivos; não chama rede nem modelo."""
import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aprende.comum import NOME, agrupar, candidatos, ler_registros  # noqa: E402

NOMES = ("FALHAS.md", "LESSONS.md", "LICOES.md")


def achar(raiz):
    raiz = Path(raiz).expanduser()
    out = []
    for nome in NOMES:
        out += [p for p in raiz.glob(f"*/{nome}")] + [p for p in raiz.glob(nome)]
    return sorted(set(out))


def sil_registrar(projeto, cands, n=5):
    import os
    sil = os.environ.get("AQA_SIL") or shutil.which("sil") or str(Path.home() / "projetos/sil-loop-r/sil.py")
    base = ["python3", sil] if sil.endswith(".py") else [sil]
    feitos = 0
    for pts, g, atual, alvo, como, vezes in cands[:n]:
        tit = ("Repete " + str(vezes) + "x: " + g[0]["problema"])[:150]
        ev = "; ".join(f"{Path(r['arquivo']).parent.name}:{r['linha']} ({r['data']})" for r in g[:6])
        r = subprocess.run(base + ["--project", projeto, "occurrence", "--title", tit, "--evidence", ev,
                                   "--correction", g[0]["correcao"][:300]], capture_output=True, text=True)
        try:
            oid = json.loads(r.stdout).get("id", "")
        except ValueError:
            oid = ""
        if r.returncode or not oid:
            print("sil: falhou —", (r.stderr or r.stdout).strip()[:200], file=sys.stderr)
            continue
        r = subprocess.run(base + ["--project", projeto, "lesson", "--occurrence", oid, "--proposal",
                                   f"Subir de {NOME[atual]} para {NOME[alvo]}: {como}", "--scope", "projeto"],
                           capture_output=True, text=True)
        if r.returncode:
            print("sil lesson: falhou —", (r.stderr or r.stdout).strip()[:200], file=sys.stderr)
            continue
        feitos += 1
    return feitos


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--raiz", default="~/projetos")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--limite", type=float, default=0.34)
    ap.add_argument("--saida")
    ap.add_argument("--sil", help="projeto com SIL Loop R iniciado para receber as propostas")
    a = ap.parse_args()
    arqs = achar(a.raiz)
    regs = [r for f in arqs for r in ler_registros(f)]
    grupos = agrupar(regs, a.limite)
    rep = [g for g in grupos if len(g) > 1]
    n_rep = sum(len(g) for g in rep)
    cruz = sorted([g for g in rep if len({Path(r["arquivo"]).parent for r in g}) > 1], key=len, reverse=True)
    cands = candidatos(regs, a.limite)
    hoje = dt.date.today().isoformat()
    lin = [f"# Jardineiro — {hoje}", "",
           f"- {len(arqs)} arquivo(s) em {len({p.parent for p in arqs})} projeto(s) · {len(regs)} registros",
           f"- **reincidência: {100 * n_rep / max(1, len(regs)):.0f}%** ({n_rep} registros em {len(rep)} grupos de 2+)",
           f"- grupos que atravessam projetos: {len(cruz)}",
           f"- candidatos a subir de degrau: {len(cands)}", "",
           "A meta da semana é a reincidência cair. Cada candidato que vira gancho/validador sai desta lista.", "",
           "## Candidatos (mais pontos primeiro)", ""]
    for k, (pts, g, atual, alvo, como, vezes) in enumerate(cands[:a.top], 1):
        projs = sorted({Path(r["arquivo"]).parent.name for r in g})
        lin += [f"{k}. **{g[0]['problema'][:100]}** — {vezes}× em {', '.join(projs)} · "
                f"{NOME[atual]} → **{NOME[alvo]}**", f"   - {como}"]
    lin += ["", "## O erro mudou de casa (mesmo grupo em projetos diferentes)", ""]
    if not cruz:
        lin.append("- nenhum")
    for g in cruz[:10]:
        projs = sorted({Path(r["arquivo"]).parent.name for r in g})
        lin.append(f"- {g[0]['problema'][:110]} — {', '.join(projs)}")
    txt = "\n".join(lin) + "\n"
    if a.saida:
        Path(a.saida).parent.mkdir(parents=True, exist_ok=True)
        Path(a.saida).write_text(txt)
        print(f"relatório: {a.saida}")
    else:
        print(txt)
    if a.sil:
        print(f"SIL: {sil_registrar(a.sil, cands)} propostas registradas em {a.sil} (decisão continua com você)")


if __name__ == "__main__":
    main()
