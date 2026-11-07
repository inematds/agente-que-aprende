#!/usr/bin/env python3
"""gancho — lição que virou trava. Hook PreToolUse do Claude Code que bloqueia o comando que já deu errado antes.

Cada lição é uma linha em ganchos.json:  {"id", "ferramenta", "padrao" (regex), "exceto" (regex, opcional),
"mensagem", "origem"}. Se o comando casa com "padrao" e não casa com "exceto", o gancho sai com código 2 e a
mensagem volta para o agente (ele corrige e tenta de novo). Sem rede, sem modelo.

Instalar (settings.json do Claude Code):
  "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command",
            "command": "python3 /caminho/agente-que-aprende/gancho.py"}]}]}
Testar uma regra:  echo '{"tool_name":"Bash","tool_input":{"command":"pkill -f x"}}' | python3 gancho.py ; echo $?
Regras extras: variável AQA_GANCHOS=/caminho/outro.json (soma às do kit). Exemplos prontos em modelos/ganchos-exemplo.json."""
import json
import os
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def regras():
    out = []
    for f in [AQUI / "ganchos.json"] + [Path(p) for p in os.environ.get("AQA_GANCHOS", "").split(":") if p]:
        try:
            out += json.loads(Path(f).read_text())
        except (OSError, ValueError):
            continue
    return out


def checar(evento, lista):
    ferr = evento.get("tool_name", "")
    ti = evento.get("tool_input") or {}
    alvo = ti.get("command") or ti.get("file_path") or ""
    if ferr == "Bash":  # só o que roda: tira corpo de heredoc e texto entre aspas (citação não é execução)
        alvo = re.sub(r"<<-?\s*['\"]?(\w+)['\"]?.*?\n\1\b", "<<HEREDOC", alvo, flags=re.S)
        alvo = re.sub(r"'[^']*'|\"(?:[^\"\\]|\\.)*\"", "''", alvo)
    for r in lista:
        if r.get("ferramenta", "Bash") not in (ferr, "*"):
            continue
        if re.search(r["padrao"], alvo) and not (r.get("exceto") and re.search(r["exceto"], alvo)):
            return r
    return None


def main():
    try:
        evento = json.load(sys.stdin)
    except ValueError:
        return 0  # entrada estranha nunca trava a sessão
    r = checar(evento, regras())
    if r:
        print(f"[agente-que-aprende/{r['id']}] {r['mensagem']}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
