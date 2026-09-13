# Handoff

_Última atualização: 2026-09-13 — último commit de código: `3247bc8` (`master`, sincronizado
com `origin`). Repo ainda **privado**._

## Estado atual

- Overlay: viewers vagam pelo rodapé com sprite LPC (andar → parar → olhar em volta),
  cor/chapéu/acessório via chat, decorações de sub/mod/broadcaster, `!dança`, cheer.
  Constantes de ritmo no topo de `web/overlay.js`.
- **Texuguito-seu-bot-amigo incorporado** (`762282c`): pontos, soundboard, TTS e
  sorteio agora fazem parte do chat-parade. O repo do texuguito foi **arquivado** no
  GitHub (`9df84db`: aviso no README apontando pro chat-parade).
  - `chat_parade/points.py` — `PointsStore` (`data/points.json`, mesmo formato do
    texuguito) e o loop de 1 ponto/min (presente em 2 checagens seguidas).
  - `chat_parade/soundboard.py` — áudios em `audios/<preço>/<nome>.<ext>`, TTS (gTTS
    pt-BR) em cache na memória, e a ponte que manda o overlay tocar.
  - `chat_parade/raffle.py` — sorteio.
  - `chat_parade/economy_commands.py` — handlers de `!pontos !addpoints !p !tts !audios
    !stop !reload !status !ping !sorteio !join`; o bot (`twitch_chat.py`) só repassa.
  - **Áudio toca no overlay** (`web/overlay.js`, fila sequencial; `!stop` pula o atual),
    servido por `/audios/...` e `/tts/<id>`. Sem overlay aberto, `!p`/`!tts` recusam
    sem cobrar. Sem pygame.
- `LICENSE` GPL-3.0 (`2dd971b`, texto canônico). README atualizado (comandos,
  "Pontos e áudios", "Vindo do texuguito", Licença).
- Dados do texuguito já copiados nesta máquina: `data/points.json` (48 saldos) e
  `audios/` (49 áudios), ambos no `.gitignore`.
- **`run.bat` faz tudo pro usuário final** (`3247bc8`): acha o Python 3.10+ (oferece
  `winget` ou abre python.org), cria `.venv` própria, só reinstala dependências quando o
  `requirements.txt` muda (carimbo em `.venv/requirements.installed`), roda
  `chat_parade.check_setup` e, se preciso, `chat_parade.oauth_setup`; `run.bat setup`
  força a configuração.
  - `check_setup.py`: exit 0 ok / 1 precisa configurar (sem `.env`, Twitch recusou,
    token inválido, faltam escopos) / 2 sem internet (inicia mesmo assim) / 3 porta do
    overlay ocupada (já aberto). Renova e salva o token quando dá certo.
  - `oauth_setup.py`: canal e `BROADCASTER_ID` vêm do login de quem autoriza (não
    pergunta mais o canal); Enter mantém ID/segredo atuais; abre o painel da Twitch com
    passo a passo; checa a porta 3000 **antes** de abrir o navegador (sem
    `SO_REUSEADDR` no Windows, que deixaria dividir a porta com outro programa);
    preserva `DATA_DIR`/`OVERLAY_PORT`/`AUDIO_DIR`/`AUDIO_VOLUME` ao reescrever o `.env`.
- Testes: `.venv` criado nesta máquina; `.venv/bin/python -m pytest` → 157 passando.
- Fim de linha: `.gitattributes` com `* text=auto eol=crlf` (LF no repo, CRLF no checkout).

## Próximos passos

0. **Gerar o `.env` com o app novo da Twitch.** Em 2026-09-13 o usuário revogou o
   token e **apagou o app antigo** (resolvendo o token vazado no histórico do
   texuguito) e criou um app novo. O `.env` desta máquina ainda tem o app apagado
   (`check_setup` confirma: "Twitch recusou"). O usuário tentou o setup e falhou porque
   o **SpacetimeDB (projeto `nos`) ocupa a porta 3000** nesta máquina: parar o
   SpacetimeDB antes de rodar `.venv/bin/python -m chat_parade.oauth_setup`. O
   segredo do app novo apareceu no terminal compartilhado com o Claude: sugerido gerar
   um "Novo segredo" nessa configuração. Quem digita as credenciais é o usuário.
1. **Rodar o `run.bat` numa máquina Windows.** Ele **nunca foi executado**: não há
   Windows/Wine nesta máquina; só a lógica Python foi testada (incluindo `check_setup`
   contra a Twitch real e o aviso de porta 3000 ocupada). Conferir: Python ausente
   (winget), primeira instalação no `.venv`, setup abrindo sozinho, `run.bat setup`,
   segunda janela avisando que já está aberto.
2. **Tornar o chat-parade público** — o usuário pediu pra **esperar**; só fazer quando
   ele mandar. Até lá, o link no README do texuguito arquivado dá 404 pra quem não é
   dono. O histórico do chat-parade já foi checado: sem tokens, `.env`/`viewers.json`
   nunca commitados. (O `HANDOFF.md` antigo cita os commits do token vazado, mas o
   token morreu junto com o app.) Comando: `gh repo edit meketreve/chat-parade --visibility public
   --accept-visibility-change-consequences`.
3. **Testar ao vivo no OBS com o chat real.** Verificado só: suíte de testes + teste de
   ponta a ponta local (servidor real + overlay no navegador + gTTS real + fila + `!stop`
   + áudio quebrado no meio da fila), **sem Twitch**. Não verificado: loop de pontos com
   chatters reais, `!sorteio` até o fim, áudio dentro do Browser Source do OBS
   ("Controlar áudio via OBS"), movimento dos viewers com o chat real.
4. **Outros clones do repositório** (ex.: a máquina Windows): depois do pull, rodar
   `git rm --cached -r -q . && git reset --hard` com o working tree limpo, pra
   reescrever os arquivos com o fim de linha novo.

## Decisões em aberto

- **Texuguito continua público e arquivado.** O token do histórico já não vale nada,
  mas o `points.json` (nicks + pontos de 48 viewers) e os áudios seguem visíveis. O
  usuário decidiu só revogar. Se quiser apagar: `gh auth refresh -h github.com -s
  delete_repo` e `gh repo delete meketreve/texuguito-seu-bot-amigo` (quem roda é o
  usuário); depois tirar o link do README do chat-parade. O clone local tem todo o
  histórico, incluindo a branch `master`.
- **`!stop` liberado pra todos** (como era no texuguito): qualquer viewer pode cortar um
  áudio que outro pagou. Talvez restringir a mod/broadcaster.
- **`!addpoints` aceita valor negativo** (como no texuguito), então o saldo pode ficar
  negativo.
- **`!dança` durante a caminhada:** hoje o viewer continua andando enquanto pula.
- **Integrações possíveis** (não pedidas): gastar pontos em chapéu/acessório, avatar
  dançar quando alguém toca um áudio.
- Checkboxes dos planos em `docs/superpowers/plans/` estão desmarcados, embora as
  features estejam feitas.

## Notas

- Overlay aberto em mais de um lugar = áudio tocando duas vezes (cada página toca).
- Em navegador comum, autoplay só funciona depois de um clique na página; no OBS toca
  direto.
- Um sorteio em andamento se perde se o app reiniciar (estado só em memória).
- Teste de áudio sem Twitch: script que monta `create_app` + `Soundboard` com um
  `ViewerStore` de viewer presente e expõe rotas de debug chamando os handlers de
  `economy_commands`; abrir `/overlay`, clicar na página e chamar as rotas.
- Teste visual do movimento sem servidor: symlink `static -> web/` e um `index.html` que
  troca `window.WebSocket` por uma classe falsa que manda um `snapshot` no construtor
  (com `<meta charset="utf-8">`, senão o ♛ sai quebrado).
- Sheets LPC: 9 colunas × 4 linhas (up, left, down, right); coluna 0 = parado, 1–8 =
  caminhada. O overlay usa as linhas "right" (espelhada pra esquerda) e "down".
- Twitchio: `Chatter.is_mod` acessa `channel.name`, então quebra em testes com
  `channel=None` quando `_mod != 1`; `is_broadcaster` vem do tag `badges`.
