#!/usr/bin/env python3
"""degrau — quais lições/falhas ainda são só TEXTO e se repetem, e para que degrau cada uma deve subir.

Uso:
  python3 degrau.py FALHAS.md [LESSONS.md ...] [--top 10] [--limite 0.34] [--saida relatorio.md]
Lê tabelas de FALHAS (data | o que quebrou | correção | tipo), LICOES (3 colunas) e listas de LESSONS ('- texto (data)').
Palpite por palavras (transparente, sem modelo). Não muda nenhum arquivo além do --saida."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aprende.comum import NOME, candidatos, ler_registros  # noqa: E402


def relatorio(regs, top, limite, titulo):
    cands = candidatos(regs, limite)
    lin = [f"# {titulo}", "",
           f"{len(regs)} registros lidos · {len(cands)} candidatos a subir de degrau "
           f"(ordem de força: arquitetura > gancho/validador > teste > checklist > texto).", ""]
    if not cands:
        lin.append("Nenhum candidato: nada se repete ou já está num degrau forte.")
    for k, (pts, g, atual, alvo, como, vezes) in enumerate(cands[:top], 1):
        r0 = g[0]
        lin += [f"## {k}. {r0['problema'][:110]}",
                f"- **pontos {pts}** · aparece {vezes}× · hoje: **{NOME[atual]}** → subir para: **{NOME[alvo]}**",
                f"- como: {como}"]
        for r in g[:5]:
            lin.append(f"  - `{Path(r['arquivo']).parent.name}/{Path(r['arquivo']).name}:{r['linha']}` "
                       f"({r['data']}) {r['correcao'][:140]}")
        lin.append("")
    return "\n".join(lin) + "\n", cands


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("arquivos", nargs="+")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--limite", type=float, default=0.34, help="semelhança mínima (Jaccard) para contar como o mesmo erro")
    ap.add_argument("--saida")
    a = ap.parse_args()
    regs = []
    for f in a.arquivos:
        if Path(f).exists():
            regs += ler_registros(f)
        else:
            print(f"aviso: {f} não existe", file=sys.stderr)
    txt, _ = relatorio(regs, a.top, a.limite, "Subir degrau — " + ", ".join(Path(f).name for f in a.arquivos))
    if a.saida:
        Path(a.saida).write_text(txt)
        print(f"relatório: {a.saida}")
    else:
        print(txt)


if __name__ == "__main__":
    main()
