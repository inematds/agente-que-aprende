# Falhas (exemplo fictício)

| data | o que quebrou | menor correção | prompt \| infra |
|---|---|---|---|
| 2026-11-06 | render caiu: `templates/pt/scene-01.html` ausente; prepare feito sem build_scene_templates (3ª vez) | rodar build_scene_templates antes do render | prompt |
| 2026-10-23 | render caiu de novo: `templates/pt/scene-01.html` ausente depois do prepare | lembrar de rodar build_scene_templates | prompt |
| 2026-10-19 | `pkill -f "servidor"` no mesmo comando matou o próprio shell (exit 144) | matar por PID com pgrep em comando separado | prompt |
| 2026-10-12 | `pkill -f "servidor web"` matou o shell do agente | matar por PID, nunca pkill -f | prompt |
| 2026-10-02 | backup sem teste de restauração | teste automático de restauração no CI | infra |
