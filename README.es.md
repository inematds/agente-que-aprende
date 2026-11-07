# agente-que-aprende

[![agente-que-aprende](guia/assets/banner-es.jpg)](https://inematds.github.io/agente-que-aprende/guia/es/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## Qué es

agente-que-aprende es un kit de cuatro scripts en Python para quien trabaja con agentes de IA de programación, como Claude Code y Codex. Lee tus sesiones y los archivos donde anotas fallas y lecciones (FALHAS.md, LESSONS.md), muestra dónde corregiste al agente y qué errores vuelven, y ayuda a convertir cada lección en una traba automática en lugar de una regla escrita más. Solo necesita Python 3; no usa internet ni API, y ninguna regla se adopta sin tu decisión.

## 📖 Guía de uso

Guía completa (landing + paso a paso): **https://inematds.github.io/agente-que-aprende/guia/es/**

Tu agente de IA comete un error, lo corriges en el chat y, en la siguiente sesión, vuelve a cometerlo. Este kit cierra ese ciclo: encuentra dónde corregiste al agente, detecta el error que vuelve a aparecer (en el mismo proyecto o en otro) y transforma la lección en una **barrera**: un gancho que impide ejecutar el comando, un validador que genera lo que falta o una prueba; en lugar de otra línea de texto que el modelo puede pasar por alto. Funciona con Claude Code y Codex, en Python puro, sin API ni conexión a la red.


## La idea en una frase

El modelo es el mismo; lo que mejora es el sistema que lo rodea. Y la corrección más sólida va primero:
**arquitectura** (hace imposible el error) > **gancho/validador** (lo bloquea) > **prueba** (lo detecta) > **texto** (se puede pasar por alto).

## Qué incluye

| Herramienta | Qué hace | Nivel |
|---|---|---|
| `retro.py` | La retrospectiva de 1 minuto: lee la sesión (`.jsonl`) y enumera dónde corregiste al agente y qué error de herramienta se repitió, con el nivel sugerido para cada uno | memoria con control |
| `degrau.py` | Lee FALHAS.md / LESSONS.md de un proyecto y muestra qué sigue siendo solo texto **y se repite**, con el nivel al que debe subir | error imposible |
| `jardineiro.py` | Lo mismo en todos los proyectos a la vez, cada semana: tasa de reincidencia, errores que «cambiaron de casa» y clasificación | ciclo externo |
| `gancho.py` + `ganchos.json` | Hook PreToolUse: cada lección se convierte en una línea de JSON (patrón → mensaje) y se bloquea el comando que ya falló, con una explicación | error imposible |
| `hooks/fim-de-sessao.sh` | Hook SessionEnd: ejecuta la retrospectiva automáticamente al cerrar la sesión | automatización |
| `modelos/` | Validador de pasos (genera lo que falta o se detiene), temporizador semanal del jardinero | — |

Se integra con [SIL Loop R](https://github.com/inematds/sil-loop-r) (`--sil <projeto>`): las propuestas se agregan como ocurrencia + lección **propuesta**; solo se convierten en regla cuando tú lo decides.

## El proceso, de principio a fin

🧠 sesión contigo · ⚙️ script/temporizador · 🤖 agente

| # | Paso | Comando | Quién |
|---|---|---|---|
| 1 | Registrar cada falla en una línea (fecha, qué falló, corrección mínima, prompt/infra) | `FALHAS.md` / `LESSONS.md` | 🧠 |
| 2 | Al final de la sesión, la retrospectiva se ejecuta sola y guarda el informe si hubo una corrección o un error repetido | `hooks/fim-de-sessao.sh` (SessionEnd) | ⚙️ |
| 3 | Leer la retrospectiva y elegir qué se convierte en lección (control humano) | `python3 retro.py <sessao.jsonl> [--sil P]` | 🧠 |
| 4 | Cada semana, el jardinero mide la reincidencia y enumera los candidatos | `python3 jardineiro.py --saida jardim/AAAA-MM-DD.md` (temporizador) | ⚙️ |
| 5 | Para cada candidato, subir de nivel: gancho en `ganchos.json`, validador en la cadena o prueba | editar `ganchos.json` / `modelos/validador-passo.sh` | 🧠 + 🤖 |
| 6 | Probar la barrera (el comando incorrecto se bloquea y el correcto pasa) | `python3 -m unittest discover -s tests` | ⚙️ |
| 7 | La semana siguiente, la reincidencia debe bajar; el candidato tratado desaparece de la lista | `jardineiro.py` otra vez | ⚙️ |

## Para empezar

```bash
git clone https://github.com/inematds/agente-que-aprende.git && cd agente-que-aprende
python3 -m unittest discover -s tests -v            # 10 testes, sem rede
python3 degrau.py caminho/do/projeto/FALHAS.md      # o que subir de degrau neste projeto
python3 jardineiro.py --raiz ~/projetos             # todos os projetos de uma vez
python3 retro.py ~/.claude/projects/<pasta>/<id>.jsonl --pergunta   # retro + pedido para colar no agente
```

Conectarlo a Claude Code (`~/.claude/settings.json`):

```json
"hooks": {
  "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 /caminho/agente-que-aprende/gancho.py"}]}],
  "SessionEnd": [{"hooks": [{"type": "command", "command": "bash /caminho/agente-que-aprende/hooks/fim-de-sessao.sh"}]}]
}
```

Temporizador semanal: copia `modelos/systemd/jardineiro.{service,timer}` a `~/.config/systemd/user/`, ajusta las rutas y
ejecuta `systemctl --user enable --now jardineiro.timer`.

## Formatos que lee

- **FALHAS.md**: tabla `| data | o que quebrou | menor correção | prompt \| infra |`
- **LICOES.md**: tabla `| data | o que quebrou | proteção |`
- **LESSONS.md**: lista `- regla en una línea (dd/mm/aaaa)`
- **Sesiones**: Claude Code (`~/.claude/projects/*/*.jsonl`) y Codex (`~/.codex/sessions/**/rollout-*.jsonl`). Solo cuentan como corrección los mensajes que escribiste tú (se excluyen los avisos de tareas, los resúmenes de compactación y las continuaciones automáticas).

## Límites

- El nivel actual y la sugerencia son **estimaciones basadas en palabras** (transparentes y ajustables en `aprende/comum.py`), no un análisis con un modelo. La decisión es tuya.
- El jardinero agrupa errores parecidos según la similitud de las palabras; los mismos errores escritos de formas muy distintas pueden quedar separados.
- Un ciclo que se ejecuta sin supervisión también puede fallar sin que nadie lo note: nada aquí adopta reglas automáticamente.

Licencia MIT.