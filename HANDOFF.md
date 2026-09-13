# Handoff

_Última atualização: 2026-09-12 — último commit de código: `66bfa9a` (`master`, sincronizado com `origin`)._

## Estado atual

- Overlay funcionando: viewers aparecem no rodapé com sprite LPC, cor/chapéu/acessório
  via chat, decorações de sub/mod/broadcaster, `!dança` e anel de cheer.
- Viewers agora **vagam**: andam até um ponto aleatório, param 1,5–5s (pose parada,
  coluna 0 da sheet), olham em volta (de frente/lados) e andam de novo.
  Lógica em `web/overlay.js` (`updateMovement`, `startWalking`, `startIdle`,
  `lookAround`, `spritePose`); constantes de ritmo no topo do arquivo.
- Working tree limpo. Fim de linha: `.gitattributes` com `* text=auto eol=crlf`
  (LF no repositório, CRLF no checkout).

## Feito na última sessão

- `de0527c` — movimento aleatório andar/parar/olhar em volta com as animações certas;
  `idle_frame_column` no `manifest.json`.
- `de0527c` — `acc_monoculo.png`: a linha "right" estava vazia (monóculo nunca
  aparecia andando); preenchida com a linha "left" espelhada.
- `370f01c` + `66bfa9a` — padronização de fim de linha e `.gitattributes`.
- Git desta máquina configurado com a identidade da conta `gh` (`meketreve`, e-mail
  noreply) e `gh auth setup-git` como credential helper.

## Próximos passos

1. **Validar o movimento ao vivo no OBS.** Até agora só foi testado num harness local
   com WebSocket falso. Conferir com o chat real e ajustar as constantes
   (`IDLE_MIN_MS`, `IDLE_MAX_MS`, `MIN_WALK_DISTANCE_PX`, `LOOK_*`,
   `FACE_FRONT_CHANCE`) se o ritmo parecer rápido/lento demais.
2. **Rodar a suíte de testes.** Não rodou na última sessão: não há `pytest` nem venv
   nesta máquina Linux. Criar um `.venv`, `pip install -r requirements.txt` e rodar
   `pytest`.
3. **Outros clones do repositório** (ex.: a máquina Windows): depois do pull, rodar
   `git rm --cached -r -q . && git reset --hard` com o working tree limpo, pra
   reescrever os arquivos já existentes com o fim de linha novo.

## Decisões em aberto

- **`!dança` durante a caminhada:** hoje o viewer continua andando enquanto pula.
  Talvez fique melhor parar e virar de frente enquanto dança — não foi pedido,
  perguntar antes de mudar.
- **Checkboxes dos planos** em `docs/superpowers/plans/` estão todos desmarcados,
  embora as features já estejam no `git log`. Confirmar e marcar, ou ignorar.

## Notas

- **Teste visual sem Twitch:** servir a pasta com um symlink `static -> web/` e um
  `index.html` que carrega `/static/overlay.js` depois de trocar `window.WebSocket`
  por uma classe falsa que, no construtor, chama `this.onmessage({data: JSON.stringify({type: "snapshot", viewers: [...]})})`.
  Colocar `<meta charset="utf-8">` senão o ♛ sai quebrado.
- Todas as sheets LPC têm 9 colunas × 4 linhas (up, left, down, right); coluna 0 é a
  pose parada, 1–8 o ciclo de caminhada. O overlay usa só as linhas "right"
  (espelhada pra esquerda) e "down" (parado de frente). A linha "up" de alguns
  acessórios é vazia, o que é esperado.
