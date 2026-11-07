# CLAUDE.md — agente-que-aprende

Kit em Python puro (sem dependências, sem rede, sem API) para transformar correções e falhas repetidas em travas.
Ferramentas: `retro.py`, `degrau.py`, `jardineiro.py`, `gancho.py` + `ganchos.json`, `hooks/fim-de-sessao.sh`. Lógica comum em `aprende/comum.py`.

- Antes de mudar qualquer heurística: `python3 -m unittest discover -s tests -v` (tem de continuar passando).
- Gancho novo = uma linha em `ganchos.json` com `origem` (de onde veio a lição) + caso no `tests/test_kit.py` (bloqueia o errado, libera o certo).
- `gancho.py` nunca pode travar a sessão por entrada estranha (sai 0).
- Nada adota regra sozinho: o SIL recebe só ocorrência + lição proposta.
- Dados de teste são fictícios. Nunca commitar relatórios reais (`jardim/`, `retro/`) nem nomes de terceiros.
- Commits: autor `inematds <inematds@gmail.com>`. Guia em `guia/` (PT, `guia/en/`, `guia/es/`). README nos 3 idiomas; ao mudar o fluxo, atualizar "O processo, do início ao fim".

## Self-learning

When I correct you, or you catch yourself making a mistake: before continuing, add the lesson as a one-line rule under ## Lessons, so it never happens again.

## Lessons

- O SIL Loop R devolve JSON no `occurrence`; ler o id com `json.loads`, nunca pela primeira palavra (07/11/2026).
- Palavra-sinal de degrau: "guard" casava com "Guardar o PID" e "Guardrail do plano"; usar o degrau mais comum do grupo, não o mais forte (07/11/2026).
- Padrão de gancho casa só o comando em posição de execução; citar o comando em texto, heredoc ou grep não pode bloquear (07/11/2026).
