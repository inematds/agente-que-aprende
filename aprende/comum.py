"""Funções comuns: ler FALHAS/LESSONS, normalizar texto, achar repetições e palpitar o degrau de proteção.
Só biblioteca padrão. Nada aqui chama rede ou modelo."""
import re
import unicodedata
from pathlib import Path

# degraus do mais fraco ao mais forte (mesma escala do SIL Loop R)
DEGRAUS = ["prose", "checklist", "test", "probe", "hook", "server"]
NOME = {"prose": "texto", "checklist": "checklist", "test": "teste", "probe": "sonda",
        "hook": "gancho/validador", "server": "servidor/arquitetura"}

PARADAS = set("""
para pela pelo pelos pelas com sem uma umas uns dos das nos nas que por mas mais menos como quando onde porque
isso esse essa este esta isto aqui ali entao tambem ainda sempre nunca depois antes cada todo toda todos todas
muito pouco outro outra sobre entre ate desde seu sua seus suas meu minha nosso nossa voce eles elas ele ela
nao sim foi era ser ter tem tinha vai vez vezes ficou fica deve deveria pode podia faz fazer feito usar usa usou
the and for with without this that from into when then than have has had was were are not but also only just
""".split())

REPETE = re.compile(r"(\d+)\s*[ªaº]\s*vez|de novo|outra vez|novamente|repet|again|same mistake|mesmo erro|"
                    r"já (?:tinha|aconteceu|vimos|falei)|voltou a", re.I)

SINAIS = {
    "server": r"arquitetur|o script (?:faz|gera|roda) sozinho|por constru|imposs[ií]vel",
    "hook": r"\bhook|gancho|pre-?commit|\bci\b|recusa|bloqueia|valida(?:dor|cao|ção)|falha se|sai(?:r)? (?:com )?1|exit 1|assert|"
            r"--strict|aborta|impede",
    "probe": r"sonda|monitor|vigia|alerta|health",
    "test": r"\bteste|\btest\b|regress[aã]o|unittest|pytest",
    "checklist": r"checklist|confer|checar|verificar|olhar a folha|lista de",
}

# o que a correção sugere fazer para subir de degrau (ordem de força)
SUGESTAO = [
    (r"pkill|rm -rf|git push|gh repo create|sudo |command not found|matou o pr[oó]prio",
     "hook", "hook PreToolUse que bloqueia (ou corrige) o comando com a mensagem da lição"),
    (r"aus[eê]nt|faltou|pulou|esqueceu|sem o passo|n[aã]o rodou|missing|skipped",
     "server", "arquitetura: o script/cadeia faz o passo sozinho (ou gera o que falta) — o erro deixa de existir"),
    (r"confer|checar|antes de|verificar|olhar",
     "hook", "validador que sai 1 antes de seguir (ou hook PreToolUse) — a conferência vira obrigatória"),
    (r"cort|vaz|sobrep|tamanho|limite|teto|caracter|dura[cç]",
     "test", "teste/medição automática com o limite (falha acima do teto)"),
]


def sem_acento(t):
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")


def tokens(t):
    t = sem_acento(t.lower())
    t = re.sub(r"`[^`]*`", lambda m: " " + m.group(0).strip("`").replace("/", " ") + " ", t)
    return {w for w in re.findall(r"[a-z0-9_]{4,}", t) if w not in PARADAS and not w.isdigit()}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def ler_registros(caminho):
    """Linhas de FALHAS.md (tabela: data | o que quebrou | correção | tipo), LICOES.md (tabela de 3 colunas)
    ou LESSONS.md (lista '- texto (data)'). Devolve dicts com arquivo, linha, data, problema, correcao, texto."""
    p = Path(caminho)
    out = []
    for n, linha in enumerate(p.read_text(errors="replace").splitlines(), 1):
        s = linha.strip()
        if s.startswith("|"):
            cel = [c.strip() for c in s.strip("|").split("|")]
            if len(cel) < 3 or not re.match(r"\d{4}-\d{2}-\d{2}|\d{2}/\d{2}", cel[0]):
                continue
            out.append({"arquivo": str(p), "linha": n, "data": cel[0], "problema": cel[1],
                        "correcao": cel[2], "tipo": cel[3] if len(cel) > 3 else "", "texto": " ".join(cel[1:3])})
        elif s.startswith("- ") and len(s) > 25:
            m = re.search(r"\((\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})\)", s)
            txt = s[2:]
            out.append({"arquivo": str(p), "linha": n, "data": m.group(1) if m else "", "problema": txt,
                        "correcao": txt, "tipo": "", "texto": txt})
    return out


def degrau_atual(texto):
    """Palpite do degrau em que a correção registrada está (o mais forte citado; padrão = texto)."""
    t = sem_acento(texto.lower())
    for d in ["server", "hook", "probe", "test", "checklist"]:
        if re.search(sem_acento(SINAIS[d]), t):
            return d
    return "prose"


def sugerir(texto):
    t = sem_acento(texto.lower())
    for padrao, alvo, como in SUGESTAO:
        if re.search(sem_acento(padrao), t):
            return alvo, como
    return "test", "teste que reproduz o erro e passa a falhar se ele voltar"


def vezes_citadas(texto):
    m = re.search(r"(\d+)\s*[ªaº]\s*vez", texto, re.I)
    return int(m.group(1)) if m else (2 if REPETE.search(texto) else 1)


def agrupar(regs, limite=0.34):
    """Grupos de registros parecidos (mesmo erro voltando). Índice invertido evita comparar tudo com tudo."""
    toks = [tokens(r["texto"]) for r in regs]
    freq = {}
    for ts in toks:
        for w in ts:
            freq[w] = freq.get(w, 0) + 1
    n = len(regs)
    raros = {w for w, f in freq.items() if f <= max(8, n // 40)}
    idx = {}
    for i, ts in enumerate(toks):
        for w in ts & raros:
            idx.setdefault(w, []).append(i)
    pai = list(range(n))

    def raiz(i):
        while pai[i] != i:
            pai[i] = pai[pai[i]]
            i = pai[i]
        return i
    vistos = set()
    for lista in idx.values():
        for a in range(len(lista)):
            for b in range(a + 1, len(lista)):
                i, j = lista[a], lista[b]
                if (i, j) in vistos:
                    continue
                vistos.add((i, j))
                if jaccard(toks[i], toks[j]) >= limite:
                    pai[raiz(i)] = raiz(j)
    grupos = {}
    for i in range(n):
        grupos.setdefault(raiz(i), []).append(regs[i])
    return [g for g in grupos.values()]


def candidatos(regs, limite=0.34):
    """Candidatos a subir de degrau, só o que se repete: (pontos, grupo, degrau, alvo, como, vezes)."""
    out = []
    for g in agrupar(regs, limite):
        vezes = max(len(g), max(vezes_citadas(r["texto"]) for r in g))
        ds = [degrau_atual(r["correcao"]) for r in g]
        atual = max(set(ds), key=lambda d: (ds.count(d), -DEGRAUS.index(d)))  # o mais comum; empate → o mais fraco
        alvo, como = sugerir(" ".join(r["texto"] for r in g))
        if vezes < 2 or DEGRAUS.index(alvo) <= DEGRAUS.index(atual):
            continue
        fraco = 2 if atual == "prose" else 1
        out.append((vezes * fraco, g, atual, alvo, como, vezes))
    out.sort(key=lambda x: (-x[0], -len(x[1])))
    return out
