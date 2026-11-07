import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
D = KIT / "tests" / "dados"
sys.path.insert(0, str(KIT))
from aprende.comum import candidatos, degrau_atual, ler_registros  # noqa: E402
import gancho  # noqa: E402
import retro  # noqa: E402


class Degrau(unittest.TestCase):
    def test_le_tabela(self):
        regs = ler_registros(D / "FALHAS.md")
        self.assertEqual(len(regs), 5)
        self.assertEqual(regs[0]["data"], "2026-11-06")

    def test_repetidos_viram_candidatos(self):
        cands = candidatos(ler_registros(D / "FALHAS.md"))
        textos = [c[1][0]["problema"] for c in cands]
        self.assertEqual(len(cands), 2, textos)          # templates e pkill; o backup não se repete
        self.assertTrue(any("scene-01" in t for t in textos))
        self.assertTrue(any("pkill" in t for t in textos))

    def test_degrau_palpite(self):
        self.assertEqual(degrau_atual("lembrar de rodar o passo"), "prose")
        self.assertEqual(degrau_atual("teste automático de restauração no CI"), "hook")
        self.assertEqual(degrau_atual("Guardar o PID ao subir"), "prose")  # 'guardar' não é gancho

    def test_ausente_sugere_arquitetura(self):
        cands = candidatos(ler_registros(D / "FALHAS.md"))
        tpl = [c for c in cands if "scene-01" in c[1][0]["problema"]][0]
        self.assertEqual(tpl[3], "server")


class Retro(unittest.TestCase):
    def test_so_correcoes_humanas(self):
        pedido, msgs, corr, erros, rep = retro.analisar(D / "sessao.jsonl")
        self.assertEqual(pedido, "faça o relatório semanal")
        self.assertEqual(len(corr), 1)                    # aviso de tarefa e resumo de compactação não contam
        self.assertIn("gráfico em barras", corr[0][2])
        self.assertEqual(len(rep), 1)                     # o mesmo ModuleNotFoundError 2x
        self.assertIn("pandas", rep[0][0])

    def test_saida_arquivo(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t) / "r.md"
            subprocess.run([sys.executable, str(KIT / "retro.py"), str(D / "sessao.jsonl"), "--saida", str(out)],
                           check=True, capture_output=True)
            self.assertIn("1 correções", out.read_text())


@unittest.skipUnless((Path.home() / "projetos/sil-loop-r/sil.py").exists(), "SIL Loop R não instalado")
class Sil(unittest.TestCase):
    def test_propostas_entram_como_licao(self):
        sil = str(Path.home() / "projetos/sil-loop-r/sil.py")
        with tempfile.TemporaryDirectory() as t:
            subprocess.run([sys.executable, sil, "--project", t, "init"], check=True, capture_output=True)
            subprocess.run([sys.executable, str(KIT / "jardineiro.py"), "--raiz", str(D), "--sil", t],
                           check=True, capture_output=True)
            exp = json.loads(subprocess.run([sys.executable, sil, "--project", t, "export"], check=True,
                                            capture_output=True, text=True).stdout)
            self.assertEqual(len(exp["occurrences"]), 2)
            self.assertEqual(len(exp["lessons"]), 2)
            self.assertEqual(len(exp["rules"]), 0)        # nada adotado sem decisão humana


class Gancho(unittest.TestCase):
    def ev(self, cmd):
        return {"tool_name": "Bash", "tool_input": {"command": cmd}}

    def test_bloqueia_e_libera(self):
        R = gancho.regras()
        self.assertEqual(gancho.checar(self.ev('pkill -f "http.server 8765"'), R)["id"], "pkill-f")
        self.assertIsNone(gancho.checar(self.ev("pgrep -af http.server"), R))
        self.assertEqual(gancho.checar(self.ev("cd /x && sudo " + "pk" + "ill -f srv"), R)["id"], "pkill-f")
        # só cita o comando (documento, heredoc, grep): não bloqueia
        self.assertIsNone(gancho.checar(self.ev("python3 - <<'E'\nt = 'o comando `" + "pk" + "ill -f` no texto'\nE"), R))
        self.assertIsNone(gancho.checar(self.ev("grep -n '" + "pk" + "ill -f' FALHAS.md"), R))
        self.assertIsNone(gancho.checar(self.ev("git commit -m 'evitar sudo " + "pk" + "ill -f srv'"), R))
        self.assertIsNone(gancho.checar({"tool_name": "Read", "tool_input": {"file_path": "pkill -f"}}, R))
        # o padrão do kit só traz a trava universal; as específicas de máquina ficam nos exemplos
        self.assertEqual([r["id"] for r in R if r in json.loads((KIT / "ganchos.json").read_text())], ["pkill-f"])

    def test_exemplos_via_aqa_ganchos(self):
        import os
        os.environ["AQA_GANCHOS"] = str(KIT / "modelos" / "ganchos-exemplo.json")
        try:
            R = gancho.regras()
        finally:
            del os.environ["AQA_GANCHOS"]
        self.assertEqual(gancho.checar(self.ev("cd x && python baixar.py"), R)["id"], "python-sem-3")
        self.assertIsNone(gancho.checar(self.ev("python3 baixar.py"), R))
        self.assertEqual(gancho.checar(self.ev("gh repo create a/b --source . --push"), R)["id"], "gh-create-master")
        self.assertIsNone(gancho.checar(self.ev("git init -b main && gh repo create a/b --source . --push"), R))

    def test_codigo_de_saida(self):
        p = subprocess.run([sys.executable, str(KIT / "gancho.py")], input=json.dumps(self.ev("pkill -f x")),
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)
        self.assertIn("pgrep", p.stderr)
        p = subprocess.run([sys.executable, str(KIT / "gancho.py")], input="lixo", capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)                 # entrada estranha nunca trava a sessão

    def test_ganchos_json_valido(self):
        for r in json.loads((KIT / "ganchos.json").read_text()):
            for k in ("id", "padrao", "mensagem", "origem"):
                self.assertIn(k, r)


if __name__ == "__main__":
    unittest.main()
