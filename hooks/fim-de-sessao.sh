#!/usr/bin/env bash
# Hook SessionEnd do Claude Code: roda a retro da sessão que acabou, em segundo plano, sem travar o fechamento.
# Relatório em ${AQA_RETRO_DIR:-~/.local/share/agente-que-aprende/retro}/<data>-<id>.md (só se houver correção ou erro repetido).
# Instalar: "hooks": {"SessionEnd": [{"hooks": [{"type": "command", "command": "bash /caminho/hooks/fim-de-sessao.sh"}]}]}
KIT="$(cd "$(dirname "$0")/.." && pwd)"
ENT=$(cat)
T=$(printf '%s' "$ENT" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("transcript_path",""))' 2>/dev/null)
[ -f "$T" ] || exit 0
DIR=${AQA_RETRO_DIR:-$HOME/.local/share/agente-que-aprende/retro}; mkdir -p "$DIR"
OUT="$DIR/$(date +%F-%H%M)-$(basename "$T" .jsonl | cut -c1-8).md"
( timeout 60 python3 "$KIT/retro.py" "$T" --saida "$OUT.tmp" >/dev/null 2>&1 &&
  if grep -qE '\*\*[1-9][0-9]* correções\*\*|\([1-9][0-9]* repetidos\)' "$OUT.tmp"; then mv "$OUT.tmp" "$OUT"; else rm -f "$OUT.tmp"; fi ) &
exit 0
