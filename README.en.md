# agente-que-aprende

[![agente-que-aprende](guia/assets/banner-en.jpg)](https://inematds.github.io/agente-que-aprende/guia/en/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## What it is

agente-que-aprende is a kit of four Python scripts for people who work with AI coding agents such as Claude Code and Codex. It reads your sessions and the files where you log failures and lessons (FALHAS.md, LESSONS.md), shows where you corrected the agent and which mistakes keep coming back, and helps turn each lesson into an automatic guard instead of one more written rule. It only needs Python 3; it uses no internet or API, and no rule is adopted without your decision.

## 📖 Usage guide

Full guide (landing + step by step): **https://inematds.github.io/agente-que-aprende/guia/en/**

Your AI agent makes a mistake, you correct it in chat, and in the next session it makes the same mistake again. This kit closes that loop: it finds where you corrected the agent, finds the mistake that keeps recurring (in the same project or another one), and turns the lesson into a **guard** — a hook that blocks the command, a validator that generates what’s missing, or a test — instead of another line of text the model can skip. Works with Claude Code and Codex, in pure Python, with no API and no network.


## The idea in one sentence

The model stays the same; what improves is the system around it. And the strongest correction comes first:
**architecture** (the mistake becomes impossible) > **hook/validator** (blocks it) > **test** (catches it) > **text** (can be skipped).

## What’s included

| Tool | What it does | Level |
|---|---|---|
| `retro.py` | The 1-minute retrospective: reads the session (`.jsonl`) and lists where you corrected the agent and which tool error repeated, with a suggested level for each | memory with a gate |
| `degrau.py` | Reads a project’s FALHAS.md / LESSONS.md and shows what is still just text **and keeps recurring**, with the level it should move up to | impossible mistake |
| `jardineiro.py` | Does the same across all projects at once, every week: recurrence rate, mistakes that “moved house,” ranking | outer loop |
| `gancho.py` + `ganchos.json` | PreToolUse hook: each lesson becomes a line of JSON (pattern → message), and the command that already went wrong is blocked with an explanation | impossible mistake |
| `hooks/fim-de-sessao.sh` | SessionEnd hook: runs the retrospective automatically when the session closes | automation |
| `modelos/` | Step validator (generates what’s missing or stops), weekly gardener timer | — |

Integrates with [SIL Loop R](https://github.com/inematds/sil-loop-r) (`--sil <projeto>`): proposals are added as an occurrence + **proposed** lesson; they only become a rule with your decision.

## The process, from start to finish

🧠 session with you · ⚙️ script/timer · 🤖 agent

| # | Step | Command | Who |
|---|---|---|---|
| 1 | Record each failure on one line (date, what broke, smallest correction, prompt/infra) | `FALHAS.md` / `LESSONS.md` | 🧠 |
| 2 | At the end of the session, the retrospective runs automatically and saves the report if there was a correction or repeated error | `hooks/fim-de-sessao.sh` (SessionEnd) | ⚙️ |
| 3 | Read the retrospective and choose what becomes a lesson (human gate) | `python3 retro.py <sessao.jsonl> [--sil P]` | 🧠 |
| 4 | Every week, the gardener measures recurrence and lists the candidates | `python3 jardineiro.py --saida jardim/AAAA-MM-DD.md` (timer) | ⚙️ |
| 5 | For each candidate, move it up a level: add a hook to `ganchos.json`, a validator to the chain, or a test | edit `ganchos.json` / `modelos/validador-passo.sh` | 🧠 + 🤖 |
| 6 | Test the guard (the wrong command is blocked, the right one passes) | `python3 -m unittest discover -s tests` | ⚙️ |
| 7 | The following week, recurrence should decrease; the addressed candidate should disappear from the list | `jardineiro.py` again | ⚙️ |

## Get started

```bash
git clone https://github.com/inematds/agente-que-aprende.git && cd agente-que-aprende
python3 -m unittest discover -s tests -v            # 10 tests, no network
python3 degrau.py caminho/do/projeto/FALHAS.md      # what to move up a level in this project
python3 jardineiro.py --raiz ~/projetos             # all projects at once
python3 retro.py ~/.claude/projects/<pasta>/<id>.jsonl --pergunta   # retrospective + request to paste into the agent
```

Connect to Claude Code (`~/.claude/settings.json`):

```json
"hooks": {
  "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 /caminho/agente-que-aprende/gancho.py"}]}],
  "SessionEnd": [{"hooks": [{"type": "command", "command": "bash /caminho/agente-que-aprende/hooks/fim-de-sessao.sh"}]}]
}
```

Weekly timer: copy `modelos/systemd/jardineiro.{service,timer}` to `~/.config/systemd/user/`, adjust the paths, and run
`systemctl --user enable --now jardineiro.timer`.

## Formats it reads

- **FALHAS.md**: table `| date | what broke | smallest correction | prompt \| infra |`
- **LICOES.md**: table `| date | what broke | protection |`
- **LESSONS.md**: list `- one-line rule (dd/mm/yyyy)`
- **Sessions**: Claude Code (`~/.claude/projects/*/*.jsonl`) and Codex (`~/.codex/sessions/**/rollout-*.jsonl`). Only messages
  you typed count as corrections (task notices, compaction summaries, and automatic continuations are excluded).

## Limitations

- The current level and suggestion are **word-based guesses** (transparent and adjustable in `aprende/comum.py`), not a
  model-based analysis. The decision is yours.
- The gardener groups similar errors by word similarity; identical errors written in very different ways may
  remain separate.
- A loop that runs without anyone watching also makes mistakes without anyone watching: nothing here adopts a rule on its own.

MIT License.