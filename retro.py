#!/usr/bin/env python3
"""retro — a retrospectiva de 1 minuto no fim da sessão: onde você corrigiu o agente e que erro se repetiu.

Uso:
  python3 retro.py <sessao.jsonl> [--saida retro.md] [--sil PROJETO] [--pergunta]
- Lê a sessão do Claude Code (~/.claude/projects/<pasta>/<id>.jsonl) ou do Codex (~/.codex/sessions/.../rollout-*.jsonl).
- Acha as CORREÇÕES do usuário ("não era isso", "de novo", "já falei", "errado"…) e os ERROS de ferramenta repetidos.
- Para cada um, propõe o degrau certo (arquitetura > gancho/validador > teste > texto).
- --sil: registra cada proposta como ocorrência + lição PROPOSTA no SIL Loop R (nada é adotado sem decisão humana).
- --pergunta: imprime o pedido de retro para colar no agente ("o que deu errado aqui? …") com este resumo junto.
Não chama rede nem modelo."""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aprende.comum import NOME, sem_acento, sugerir  # noqa: E402
from jardineiro import sil_registrar  # noqa: E402

CORRECAO = re.compile(sem_acento(
    r"\bn[aã]o (?:era|é|e) (?:isso|assim|esse|essa)|errad|de novo|outra vez|novamente|j[aá] (?:falei|disse|pedi)|"
    r"t[aá] errado|faltou|esqueceu|n[aã]o (?:fa[cç]a|use|mexa|quero|gostei|funcionou)|pare de|"
    r"por que (?:voc[eê] )?(?:fez|n[aã]o)|eu (?:pedi|disse)|corrig|reprov|"
    r"\bwrong\b|\bagain\b|i (?:said|told you|asked)|not what i"), re.I)


def textos(conteudo):
    if isinstance(conteudo, str):
        return [conteudo]
    out = []
    for c in conteudo or []:
        if isinstance(c, dict) and c.get("type") in ("text", "input_text"):
            out.append(c.get("text", ""))
    return out


def ler_sessao(caminho):
    """Devolve (mensagens do usuário [(n, ts, texto)], erros de ferramenta [(n, texto)])."""
    msgs, erros = [], []
    with open(caminho, errors="replace") as fh:
        linhas = fh.readlines()
    for n, linha in enumerate(linhas, 1):
        try:
            d = json.loads(linha)
        except ValueError:
            continue
        o = d.get("origin")
        humano = not d.get("isCompactSummary") and d.get("promptSource") not in ("system", "sdk") and \
            (not isinstance(o, dict) or o.get("kind") == "human")
        if d.get("type") == "user" and not d.get("isMeta") and not d.get("isSidechain"):  # Claude Code
            c = d.get("message", {}).get("content")
            if isinstance(c, list):
                for x in c:
                    if isinstance(x, dict) and x.get("type") == "tool_result" and x.get("is_error"):
                        cont = x.get("content")
                        t = cont if isinstance(cont, str) else " ".join(textos(cont))
                        erros.append((n, t))
            for t in textos(c) if humano else []:
                msgs.append((n, d.get("timestamp", ""), t))
        p = d.get("payload") or {}
        if d.get("type") == "response_item":  # Codex
            if p.get("type") == "message" and p.get("role") == "user":
                for t in textos(p.get("content")):
                    msgs.append((n, d.get("timestamp", ""), t))
            if p.get("type") == "function_call_output":
                out = str(p.get("output", ""))
                if re.search(r'"exit_code":\s*[1-9]|Exit code:? [1-9]', out):
                    erros.append((n, out))
    # descarta mensagens do sistema/ganchos (<system-reminder>, <command-…>, avisos de interrupção)
    msgs = [(n, ts, t.strip()) for n, ts, t in msgs
            if t.strip() and not t.lstrip().startswith("<") and "[Request interrupted" not in t
            and not t.startswith("This session is being continued")]
    return msgs, erros


def chave_erro(t):
    ls = [l.strip() for l in t.strip().splitlines() if l.strip()]
    if ls and re.match(r"Exit code:? \d+$", ls[0]):
        ls = ls[1:] or ls
    exc = [l for l in ls if re.match(r"[\w.]*(Error|Exception)\b|error:|fatal:|ERRO", l)]
    linha = (exc[-1] if exc else ls[0] if ls else "")[:160]
    return re.sub(r"\d+", "N", re.sub(r"/[\w./-]+", "<arq>", linha)).strip()


def analisar(caminho):
    msgs, erros = ler_sessao(caminho)
    pedido = msgs[0][2] if msgs else ""
    corr = [(n, ts, t) for n, ts, t in msgs[1:] if CORRECAO.search(sem_acento(t))]
    grupos = {}
    for n, t in erros:
        grupos.setdefault(chave_erro(t), []).append(n)
    repetidos = sorted([(k, v) for k, v in grupos.items() if len(v) > 1], key=lambda x: -len(x[1]))
    return pedido, msgs, corr, erros, repetidos


def relatorio(caminho, pedido, msgs, corr, erros, repetidos):
    lin = [f"# Retro — {Path(caminho).name}", "",
           f"- pedido: {pedido[:200]}",
           f"- {len(msgs)} mensagens suas · **{len(corr)} correções** · {len(erros)} erros de ferramenta "
           f"({len(repetidos)} repetidos)", "", "## Onde você corrigiu o agente", ""]
    propostas = []
    for n, ts, t in corr:
        alvo, como = sugerir(t)
        lin.append(f"- linha {n} {ts[:16]}: “{t[:220]}”")
        lin.append(f"  - subir para **{NOME[alvo]}**: {como}")
        propostas.append((t, f"{Path(caminho).name}:{n}", alvo, como))
    if not corr:
        lin.append("- nenhuma correção encontrada")
    lin += ["", "## Erros que se repetiram na sessão", ""]
    for k, ns in repetidos[:10]:
        alvo, como = sugerir(k)
        lin.append(f"- {len(ns)}× `{k[:150]}` (linhas {', '.join(map(str, ns[:6]))})")
        lin.append(f"  - subir para **{NOME[alvo]}**: {como}")
        propostas.append((f"Erro repetido {len(ns)}x: {k}", f"{Path(caminho).name}:{ns[0]}", alvo, como))
    if not repetidos:
        lin.append("- nenhum")
    lin += ["", "## Decisão (sua)", "",
            "Marque o que vira proposta. Só a lição aprovada entra no AGENTS.md/CLAUDE.md — e de preferência como "
            "gancho, teste ou validador, não como mais uma linha de texto.", ""]
    return "\n".join(lin) + "\n", propostas


PERGUNTA = """Faça a retrospectiva desta sessão.
1. O que deu errado aqui? O que dava para ter feito melhor?
2. Leia as correções que eu fiz (resumo abaixo) e as mudanças no repositório.
3. Para cada problema, proponha a correção MAIS FORTE possível, nesta ordem: tornar o erro impossível (arquitetura/script)
   > bloquear com tipo, lint, CI ou hook > pegar com um teste > só então uma regra escrita.
4. Devolva uma lista por gravidade. Não aplique nada: eu escolho.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("sessao")
    ap.add_argument("--saida")
    ap.add_argument("--sil", help="projeto com SIL Loop R iniciado para receber as propostas")
    ap.add_argument("--pergunta", action="store_true")
    a = ap.parse_args()
    pedido, msgs, corr, erros, repetidos = analisar(a.sessao)
    txt, propostas = relatorio(a.sessao, pedido, msgs, corr, erros, repetidos)
    if a.pergunta:
        txt = PERGUNTA + "\n---\n" + txt
    if a.saida:
        Path(a.saida).parent.mkdir(parents=True, exist_ok=True)
        Path(a.saida).write_text(txt)
        print(f"retro: {a.saida} ({len(corr)} correções, {len(repetidos)} erros repetidos)")
    else:
        print(txt)
    if a.sil and propostas:
        cands = [(0, [{"problema": t, "correcao": t, "arquivo": ev, "linha": 0, "data": ""}], "prose", alvo, como, 1)
                 for t, ev, alvo, como in propostas]
        print(f"SIL: {sil_registrar(a.sil, cands, n=len(cands))} propostas registradas (decisão continua com você)")


if __name__ == "__main__":
    main()
