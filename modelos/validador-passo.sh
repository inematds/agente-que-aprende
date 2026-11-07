#!/usr/bin/env bash
# MODELO de validador ("erro impossível" no meio de uma cadeia): antes de seguir, confere que o passo anterior deixou
# o que devia. Se faltar, GERA (melhor) ou sai 1 com a lição na mensagem. Exemplo real: o render falhava 4x porque
# templates/pt/scene-01.html não existia (prepare sem build_scene_templates).
# Uso na cadeia:  bash validador-passo.sh "$OUT/v1/templates/pt/scene-01.html" "python3 engine/build_scene_templates.py"
ARQ=${1:?arquivo esperado}; GERA=${2:-}
[ -s "$ARQ" ] && exit 0
if [ -n "$GERA" ]; then
  echo "validador: $ARQ ausente — gerando: $GERA" >&2
  bash -c "$GERA" && [ -s "$ARQ" ] && exit 0
fi
echo "validador: FALTA $ARQ — o passo anterior não terminou; não sigo (lição: gerar antes de renderizar)" >&2
exit 1
