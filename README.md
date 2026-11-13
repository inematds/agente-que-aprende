# agente-que-aprende

[![agente-que-aprende](guia/assets/banner.jpg)](https://inematds.github.io/agente-que-aprende/guia/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## O que é

O agente-que-aprende é um kit de quatro scripts em Python para quem trabalha com agentes de IA de programação, como o Claude Code e o Codex. Ele lê as suas sessões e os arquivos onde você anota falhas e lições (FALHAS.md, LESSONS.md), mostra onde você corrigiu o agente e quais erros voltam, e ajuda a transformar cada lição numa trava automática em vez de mais uma regra escrita. Precisa só de Python 3; não usa internet nem API, e nenhuma regra é adotada sem a sua decisão.

## 📖 Guia de uso

Guia completo (landing + passo a passo): **https://inematds.github.io/agente-que-aprende/guia/**

🎬 Vídeo: https://www.youtube.com/watch?v=bnLvmYcP4PI

O seu agente de IA erra, você corrige no chat, e na sessão seguinte ele erra igual. Este kit fecha esse ciclo: acha onde
você corrigiu o agente, acha o erro que volta (no mesmo projeto ou em outro) e transforma a lição em **trava** — um
gancho que impede o comando, um validador que gera o que falta, um teste — em vez de mais uma linha de texto que o modelo
pode pular. Funciona com Claude Code e Codex, em Python puro, sem API e sem rede.


## A ideia em uma frase

O modelo é o mesmo; o que melhora é o sistema em volta dele. E a correção mais forte vem primeiro:
**arquitetura** (o erro fica impossível) > **gancho/validador** (bloqueia) > **teste** (pega) > **texto** (pode ser pulado).

## O que tem

| Ferramenta | O que faz | Degrau |
|---|---|---|
| `retro.py` | A retrospectiva de 1 minuto: lê a sessão (`.jsonl`) e lista onde você corrigiu o agente e que erro de ferramenta se repetiu, com o degrau sugerido para cada um | memória com portão |
| `degrau.py` | Lê FALHAS.md / LESSONS.md de um projeto e mostra o que ainda é só texto **e se repete**, com o degrau para onde deve subir | erro impossível |
| `jardineiro.py` | O mesmo em todos os projetos de uma vez, toda semana: taxa de reincidência, erros que "mudaram de casa", ranking | loop de fora |
| `gancho.py` + `ganchos.json` | Hook PreToolUse: cada lição vira uma linha de JSON (padrão → mensagem) e o comando que já deu errado é bloqueado com a explicação | erro impossível |
| `hooks/fim-de-sessao.sh` | Hook SessionEnd: roda a retro sozinho quando a sessão fecha | automação |
| `modelos/` | Validador de passo (gera o que falta ou para), timer semanal do jardineiro, exemplos de ganchos (`ganchos-exemplo.json`) | — |

Integra com o [SIL Loop R](https://github.com/inematds/sil-loop-r) (`--sil <projeto>`): as propostas entram como
ocorrência + lição **proposta**; só viram regra com a sua decisão.

## O processo, do início ao fim

🧠 sessão com você · ⚙️ script/timer · 🤖 agente

| # | Passo | Comando | Quem |
|---|---|---|---|
| 1 | Registrar cada falha numa linha (data, o que quebrou, menor correção, prompt/infra) | `FALHAS.md` / `LESSONS.md` | 🧠 |
| 2 | No fim da sessão, a retro roda sozinha e guarda o relatório se houve correção ou erro repetido | `hooks/fim-de-sessao.sh` (SessionEnd) | ⚙️ |
| 3 | Ler a retro e escolher o que vira lição (portão humano) | `python3 retro.py <sessao.jsonl> [--sil P]` | 🧠 |
| 4 | Toda semana, o jardineiro mede a reincidência e lista os candidatos | `python3 jardineiro.py --saida jardim/AAAA-MM-DD.md` (timer) | ⚙️ |
| 5 | Para cada candidato, subir o degrau: gancho no `ganchos.json`, validador na cadeia ou teste | editar `ganchos.json` / `modelos/validador-passo.sh` | 🧠 + 🤖 |
| 6 | Testar a trava (o comando errado é bloqueado, o certo passa) | `python3 -m unittest discover -s tests` | ⚙️ |
| 7 | Na semana seguinte, a reincidência tem que cair; o candidato tratado some da lista | `jardineiro.py` de novo | ⚙️ |

## Começar

```bash
git clone https://github.com/inematds/agente-que-aprende.git && cd agente-que-aprende
python3 -m unittest discover -s tests -v            # 10 testes, sem rede
python3 degrau.py caminho/do/projeto/FALHAS.md      # o que subir de degrau neste projeto
python3 jardineiro.py --raiz ~/projetos             # todos os projetos de uma vez
python3 retro.py ~/.claude/projects/<pasta>/<id>.jsonl --pergunta   # retro + pedido para colar no agente
```

Ligar no Claude Code (`~/.claude/settings.json`):

```json
"hooks": {
  "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 /caminho/agente-que-aprende/gancho.py"}]}],
  "SessionEnd": [{"hooks": [{"type": "command", "command": "bash /caminho/agente-que-aprende/hooks/fim-de-sessao.sh"}]}]
}
```

O `ganchos.json` do kit traz só a trava universal (`pkill -f`). Travas da sua máquina vão num arquivo seu, ligado por `AQA_GANCHOS=/caminho/meus.json` antes do comando do hook. O gancho funciona no Claude Code; no Codex, a retro e o jardineiro já funcionam.

Timer semanal: copiar `modelos/systemd/jardineiro.{service,timer}` para `~/.config/systemd/user/`, ajustar os caminhos e
`systemctl --user enable --now jardineiro.timer`.

## Formatos que ele lê

- **FALHAS.md**: tabela `| data | o que quebrou | menor correção | prompt \| infra |`
- **LICOES.md**: tabela `| data | o que quebrou | proteção |`
- **LESSONS.md**: lista `- regra em uma linha (dd/mm/aaaa)`
- **Sessões**: Claude Code (`~/.claude/projects/*/*.jsonl`) e Codex (`~/.codex/sessions/**/rollout-*.jsonl`). Só as mensagens
  digitadas por você contam como correção (avisos de tarefa, resumos de compactação e continuações automáticas ficam fora).

## Limites

- O degrau atual e a sugestão são **palpites por palavras** (transparentes, ajustáveis em `aprende/comum.py`), não uma
  análise por modelo. A decisão é sua.
- O jardineiro junta erros parecidos por semelhança de palavras; erros iguais escritos de jeitos muito diferentes podem
  ficar separados.
- Um loop que roda sem ninguém olhando também erra sem ninguém olhando: nada aqui adota regra sozinho.

Licença MIT.
