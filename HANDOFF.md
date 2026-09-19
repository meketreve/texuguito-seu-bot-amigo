# Handoff

_Última atualização: 2026-09-19 — último commit de código: "Rename the package to texuguito and add run.sh" (`master`, sincronizado
com `origin`). Repo **público** desde 2026-09-17._

## Estado atual

- **Repo público** (2026-09-17), descrição "Bot de comandos pra Twitch com overlay pixel
  art: desfile do chat no rodapé, pontos, áudios e TTS". Antes disso, varredura de todos
  os 61 commits e 226 blobs: sem credenciais, sem dados pessoais, sem caminhos da máquina,
  autor sempre o e-mail noreply; sem issues/PRs/releases/wiki. Repetir essa varredura
  antes de commitar qualquer coisa nova que cite caminhos locais ou credenciais.
- **Projeto renomeado pra Texuguito** (2026-09-13): o repo do GitHub virou
  `meketreve/texuguito-seu-bot-amigo` (o `chat-parade` antigo redireciona; o remote local
  já aponta pro nome novo). Nome visível trocado em README, `CLAUDE.md`, `run.bat`,
  mensagens do console (`[texuguito]`), overlay e respostas do bot.
  O repo antigo do Texuguito (só o bot) foi **apagado** do GitHub pelo usuário, e a pasta
  local dele (a do `bot.py` antigo) foi
  **apagada sem backup** em 2026-09-19, por decisão do usuário — o histórico dela, inclusive
  a branch `master` que só existia ali, não existe mais em lugar nenhum. Os dados dela já
  tinham sido copiados e conferidos (48 saldos e 49 áudios idênticos).
- **Pacote e pasta renomeados** (2026-09-19): `chat_parade/` virou `texuguito/` e todas as
  menções no código, testes, `run.bat`/`run.sh`, README e neste arquivo foram trocadas
  (os planos/specs em `docs/superpowers/` ficaram como estão, são registro histórico).
  158 testes passando depois da troca. A pasta local virou `texuguito-seu-bot-amigo`
  (a `.venv` foi refeita do zero pelo `run.sh` depois da mudança, já que a antiga tinha
  caminhos absolutos da pasta velha).

- Overlay: viewers vagam pelo rodapé com sprite LPC (andar → parar → olhar em volta),
  cor/chapéu/acessório via chat, decorações de sub/mod/broadcaster, `!dança`, cheer.
  Constantes de ritmo no topo de `web/overlay.js`.
- **Bot do Texuguito original incorporado** (`762282c`): pontos, soundboard, TTS e
  sorteio.
  - `texuguito/points.py` — `PointsStore` (`data/points.json`, mesmo formato do
    texuguito) e o loop de 1 ponto/min (presente em 2 checagens seguidas).
  - `texuguito/soundboard.py` — áudios em `audios/<preço>/<nome>.<ext>`, TTS (gTTS
    pt-BR) em cache na memória, e a ponte que manda o overlay tocar.
  - `texuguito/raffle.py` — sorteio.
  - `texuguito/economy_commands.py` — handlers de `!pontos !addpoints !p !tts !audios
    !stop !reload !status !ping !sorteio !join`; o bot (`twitch_chat.py`) só repassa.
  - **Áudio toca no overlay** (`web/overlay.js`, fila sequencial; `!stop` pula o atual),
    servido por `/audios/...` e `/tts/<id>`. Sem overlay aberto, `!p`/`!tts` recusam
    sem cobrar. Sem pygame.
- `LICENSE` GPL-3.0 (`2dd971b`, texto canônico). README atualizado (comandos,
  "Pontos e áudios", "Vindo da versão antiga do Texuguito", Licença).
- Dados do texuguito já copiados nesta máquina: `data/points.json` (48 saldos) e
  `audios/` (49 áudios), ambos no `.gitignore`.
- **`run.bat` faz tudo pro usuário final** (`3247bc8`): acha o Python 3.10+ (oferece
  `winget` ou abre python.org), cria `.venv` própria, só reinstala dependências quando o
  `requirements.txt` muda (carimbo em `.venv/requirements.installed`), roda
  `texuguito.check_setup` e, se preciso, `texuguito.oauth_setup`; `run.bat setup`
  força a configuração.
  - `check_setup.py`: exit 0 ok / 1 precisa configurar (sem `.env`, Twitch recusou,
    token inválido, faltam escopos) / 2 sem internet (inicia mesmo assim) / 3 porta do
    overlay ocupada (já aberto). Renova e salva o token quando dá certo.
  - `oauth_setup.py`: canal e `BROADCASTER_ID` vêm do login de quem autoriza (não
    pergunta mais o canal); Enter mantém ID/segredo atuais; abre o painel da Twitch com
    passo a passo; checa a porta de retorno **antes** de abrir o navegador (sem
    `SO_REUSEADDR` no Windows, que deixaria dividir a porta com outro programa);
    preserva `DATA_DIR`/`OVERLAY_PORT`/`AUDIO_DIR`/`AUDIO_VOLUME` ao reescrever o `.env`.
- **`run.sh` (Linux/Mac)**: equivalente do `run.bat`. Acha um Python 3.10+, cria/conserta
  a `.venv`, reinstala dependências só quando o `requirements.txt` muda (mesmo carimbo
  `.venv/requirements.installed`), roda `check_setup` e, se preciso, `oauth_setup`, e
  então `exec` no `texuguito.main`. `./run.sh setup` força a configuração e
  `./run.sh test` roda o pytest. Sem Python, mostra o comando de instalação do sistema
  (apt/dnf/pacman/zypper/brew) em vez de instalar sozinho com sudo. `.gitattributes`
  ganhou `*.sh text eol=lf` (o `eol=crlf` global quebraria o shebang).
  - Testado nesta máquina: `./run.sh test` (158 testes), branch de porta ocupada
    (exit 3 → não inicia) e, num diretório de sandbox com módulos falsos, a criação da
    `.venv` do zero, o pulo da reinstalação, a `.venv` quebrada sendo refeita, o desvio
    pra configuração, o `setup` e o setup que falha. **Não** testado: `oauth_setup` real
    pelo `run.sh` e o caminho "Python ausente".
- **Twitch conectada com o app novo** (2026-09-13): o app antigo foi apagado pelo usuário
  (o token vazado no histórico do texuguito morreu junto); `.env` gerado pelo
  `oauth_setup`, `check_setup` OK e o bot entrou no chat de `meketreve` num teste de 15s.
- Testes: `.venv` criado nesta máquina; `.venv/bin/python -m pytest` → 158 passando.
- Fim de linha: `.gitattributes` com `* text=auto eol=crlf` (LF no repo, CRLF no checkout).

## Próximos passos

1. **Rodar o `run.bat` numa máquina Windows.** Ele **nunca foi executado**: não há
   Windows/Wine nesta máquina; só a lógica Python foi testada (incluindo `check_setup`
   contra a Twitch real e o aviso de porta de retorno ocupada). Conferir: Python ausente
   (winget), primeira instalação no `.venv`, setup abrindo sozinho, `run.bat setup`,
   segunda janela avisando que já está aberto.
2. **Terminar o teste ao vivo no OBS.** Já verificado em 2026-09-19, com a Twitch real:
   o app conectou ao chat de `meketreve`, o overlay virou Browser Source no OBS
   (`http://localhost:8901/overlay`, com "Controlar áudio via OBS" marcado) e o `!pontos`
   respondeu no chat. O loop de pontos também rodou (escreveu em `data/points.json`).
   **Ainda não verificado:** `!p`/`!tts` tocando dentro do OBS com o áudio no mixer,
   `!sorteio` até o fim, movimento dos viewers durante uma live de verdade.
3. **Outros clones do repositório** (ex.: a máquina Windows): depois do pull, rodar
   `git rm --cached -r -q . && git reset --hard` com o working tree limpo, pra
   reescrever os arquivos com o fim de linha novo.

## Decisões em aberto

- **Recursos do Texuguito antigo que não vieram:** banner/tabelas coloridas (`rich`), log
  das mensagens do chat no console e em `logs/`, build `.exe` (PyInstaller). Portar se o
  usuário pedir (o log do chat é o mais provável).
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

- **Painéis (docks) da Twitch no OBS do usuário não funcionam — não é bug do projeto.**
  O OBS está em modo "chave de transmissão", sem conta conectada, então o navegador
  embutido (CEF) fica anônimo: os cookies dele só têm `unique_id`/`api_token`, sem
  `auth-token`. Resultado: o chat do painel aceita o texto e não envia, o dock de título
  não muda nada, e a fonte `alertas` loga `unauthenticated`. O usuário tentou conectar a
  conta em 2026-09-19, não pegou, e desligou os painéis; usa o chat pelo navegador normal.
  Se aparecer de novo como "os comandos não funcionam", o bot não é o culpado — testar
  mandando o comando pelo chat do site antes de investigar o código.

- Porta de retorno do OAuth: **17563** (era 3000, que conflita com servidores de dev).
  Apps antigos só com a 3000 dão `redirect_mismatch` na Twitch; basta adicionar a nova.
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
