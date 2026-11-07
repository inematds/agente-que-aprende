# FALHAS — agente-que-aprende (mais recente no topo)

| data | o que quebrou | menor correção | prompt \| infra |
|---|---|---|---|
| 2026-11-07 | gancho `pkill-f` barrou um heredoc que só CITAVA o comando no texto do guia (falso positivo; o revisor já tinha avisado) | regex só casa `pkill` em posição de comando (início, após ; & \| ( ou sudo/timeout) + testes de citação/heredoc/grep | prompt |
| 2026-11-07 | `--sil` registrava as ocorrências mas nenhuma lição: o id era lido como a 1ª palavra da saída, que é JSON | `json.loads(saida)["id"]` + teste de integração com o SIL | prompt |
| 2026-11-07 | retro contava resumo de compactação e avisos de tarefa como "correção do usuário" | só mensagem com `origin.kind == human` (ou sem origin, sessões antigas) | prompt |
