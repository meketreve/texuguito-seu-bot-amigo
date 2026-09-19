# Texuguito - Seu Bot Amigo

Bot pra live na Twitch com overlay pixel art:

- **Desfile do chat:** todo mundo assistindo aparece andando no rodapé da
  stream, com avatar gerado automaticamente e personalizável via comandos no
  chat.
- **Pontos do canal:** quem assiste ganha pontos por tempo no chat e gasta
  tocando áudios (`!p`), mandando mensagens em voz (`!tts`) ou participando de
  sorteios. Os áudios tocam pelo próprio overlay, então o OBS captura junto
  com o Browser Source.

## Setup

No Windows, é só dar dois cliques no **`run.bat`**. No Linux/Mac, rode
**`./run.sh`** num terminal. Os dois cuidam de tudo:

1. **Python:** se não tiver o Python 3.10+, o `run.bat` oferece instalar pelo
   `winget` (ou abre a página de download); o `run.sh` mostra o comando de
   instalação do seu sistema (`apt`, `dnf`, `pacman`, `brew`...).
2. **Dependências:** instala tudo numa pasta `.venv` própria, sem mexer no
   Python do sistema. Só reinstala quando o `requirements.txt` muda.
3. **Twitch:** confere se as credenciais do `.env` ainda funcionam. Na
   primeira vez, ou se o app da Twitch foi apagado, o acesso foi revogado ou o
   Texuguito passou a precisar de uma permissão nova, ele abre a
   configuração sozinho: mostra o passo a passo pra criar o app no painel da
   Twitch, pede o ID e o segredo do cliente e abre o navegador pra você
   autorizar (faça login com a conta **dona do canal**; o canal é descoberto
   por ela).
4. **Inicia** o Texuguito. Se ele já estiver aberto em outra janela, avisa em
   vez de abrir duas vezes.

Pra trocar de app ou de conta, rode `run.bat setup` (ou `./run.sh setup`). Na
configuração, Enter mantém o ID e o segredo atuais. O `./run.sh test` roda a
suíte de testes.

O app da Twitch precisa ter `http://localhost:17563` nas URLs de
redirecionamento OAuth, e essa porta precisa estar livre durante a
configuração. Apps configurados antes com `http://localhost:3000` só precisam
adicionar a URL nova no painel da Twitch. As
permissões pedidas são só as que o app usa:
`chat:read chat:edit moderator:read:chatters bits:read`.

Manualmente, sem os scripts:

1. `python -m venv .venv` e `.venv/bin/pip install -r requirements.txt`
2. `.venv/bin/python -m texuguito.oauth_setup` (configura a Twitch e escreve o `.env`)
3. Rode os testes: `.venv/bin/python -m pytest`
4. Suba o app: `.venv/bin/python -m texuguito.main`

O processo não abre navegador nenhum — ele imprime no console algo como:

```
[texuguito] overlay pronto em: http://localhost:8901/overlay
[texuguito] cole essa URL como Browser Source no OBS.
```

Cole essa URL num Browser Source do OBS (largura/altura à sua escolha, fundo
já é transparente). Marque **"Controlar áudio via OBS"** nas propriedades do
Browser Source pra os áudios do `!p`/`!tts` aparecerem no mixer do OBS com
volume próprio. Deixe o overlay aberto em **um** lugar só: cada página aberta
toca os áudios, então com o OBS e uma aba do navegador abertos ao mesmo tempo
o som sai duas vezes. Com o overlay fechado, o `!p` e o `!tts` recusam o
pedido sem cobrar pontos.

## Comandos do chat

| Comando | Quem pode | Efeito |
| --- | --- | --- |
| `!cor <nome ou hex>` | Todos, no próprio avatar | Troca a cor do corpo. Nome em português (ex: `azul`), inglês (ex: `blue`) ou hex (`#rrggbb`). |
| `!resetcor` | Todos, no próprio avatar | Volta pra cor gerada pela seed. |
| `!chapeu <opção>` | Todos, no próprio avatar | Troca o chapéu. Ver opções abaixo. |
| `!acessorio <opção>` | Todos, no próprio avatar | Troca o acessório. Ver opções abaixo. |
| `!nick <apelido>` | Todos, no próprio avatar | Nome exibido no rodapé. |
| `!dança` (ou `!danca`) | Todos, no próprio avatar | Dispara uma animação por alguns segundos. |
| `!avatarmod <usuario> <cor>` | Mod/Broadcaster | Força a cor do avatar de outro viewer. |
| `!pontos` (ou `!pts`) | Todos | Mostra seu saldo de pontos. |
| `!p <nome>` (ou `!play`) | Todos | Toca um áudio, pagando o preço dele em pontos. Cooldown de 1 minuto entre áudios. |
| `!audios` (ou `!sons`, `!sounds`) | Todos | Lista os áudios disponíveis, agrupados por preço. |
| `!tts <mensagem>` | Todos | Lê a mensagem em voz alta (custa 200 pontos). |
| `!stop` | Todos | Para o áudio que está tocando. |
| `!join` | Todos | Entra no sorteio em andamento. |
| `!status` / `!ping` | Todos | Confere se o bot está online. |
| `!addpoints <usuario> <qtd>` (ou `!dar`, `!give`) | Mod/Broadcaster | Dá pontos pra alguém. |
| `!reload` | Mod/Broadcaster | Relê a pasta de áudios (pra adicionar áudio sem reiniciar). |
| `!sorteio <pontos> <minutos>` | Broadcaster | Abre um sorteio; no fim, um dos que deram `!join` leva os pontos. |
| `!comandos` (ou `!ajuda`, `!help`) | Todos | Lista os comandos disponíveis no chat. |

Decorações automáticas (sem comando): sub ativo ganha borda dourada, mod
ganha a etiqueta "MOD", broadcaster ganha uma coroa (♛), e dar cheer solta um
anel dourado ao redor do avatar por alguns segundos.

### Chapéus e acessórios disponíveis

`!chapeu`: `boné`, `coroa`, `chifres`, `tricornio`, `bicorne`, `cartola`,
`tiara`, `coco`, `natalino`, `mago`, `viking`, `elmo`, `legionario`,
`bandana`, `capuz`, `faixa`, `nenhum`.

`!acessorio`: `óculos`, `capa`, `asas`, `colar`, `cachecol`, `laco`,
`tapaolho`, `oculosescuros`, `monoculo`, `asasmorcego`, `asasborboleta`,
`asaslibelula`, `nenhum`.

## Pontos e áudios

- Quem está no chat ganha **1 ponto por minuto** (precisa aparecer em duas
  checagens seguidas, com 1 minuto entre elas). Os saldos ficam em
  `data/points.json`.
- Os áudios do `!p` ficam em `audios/`, numa subpasta com o **preço em pontos**
  como nome. O nome do arquivo (sem extensão) é o que o viewer digita:

  ```
  audios/
    20/oof.mp3      → !p oof custa 20 pontos
    100/bonk.ogg    → !p bonk custa 100 pontos
  ```

  Aceita `.mp3`, `.wav` e `.ogg`. A pasta é criada sozinha na primeira vez que
  o app sobe e não vai pro git (cada streamer usa os seus áudios). Depois de
  adicionar arquivos, use `!reload` no chat.
- O `!tts` usa o Google TTS (pt-BR), então precisa de internet. Se der erro,
  os pontos são devolvidos.
- Opcional no `.env`: `AUDIO_DIR` (outra pasta de áudios) e `AUDIO_VOLUME`
  (0.0 a 1.0, padrão 1.0).

### Vindo da versão antiga do Texuguito

A versão antiga (só o bot de pontos, com `bot.py`) guardava os mesmos dados:
copie o `points.json` dela pra `data/points.json` e os saldos continuam, e as
subpastas de `files/` pra `audios/`. O `.env` antigo também serve, desde que o
app da Twitch dele ainda exista; se não, o `run.bat`/`run.sh` percebe e abre a
configuração.

## Se o token expirar

Não precisa fazer nada: toda vez que o app sobe, ele renova o token sozinho
usando o `REFRESH_TOKEN` guardado no `.env`. Se a Twitch recusar (app apagado,
segredo trocado, acesso revogado), o `run.bat`/`run.sh` percebe e abre a
configuração de novo. Fora deles, rode `python -m texuguito.check_setup` pra saber se
as credenciais funcionam e `python -m texuguito.oauth_setup` pra refazer.

## Créditos

Os avatares usam sprites do [Liberated Pixel Cup](https://lpc.opengameart.org)
(CC-BY-SA 3.0 / GPL 3.0), gerados via o
[Universal LPC Spritesheet Character Generator](https://liberatedpixelcup.github.io/Universal-LPC-Spritesheet-Character-Generator/).

- `body/bodies/male/walk.png` — 'Thick' Male Revised Run/Climb by JaidynReiman
  (based on ElizaWy's LPC Revised). Autores: bluecarrot16, JaidynReiman,
  Benjamin K. Smith (BenCreating), Evert, Eliza Wyatt (ElizaWy), TheraHedwig,
  MuffinElZangano, Durrani, Johannes Sjölund (wulax), Stephen Challener (Redshrike).
- `head/heads/human/male/walk.png` — original head by Redshrike, tweaks by
  BenCreating, modular version by bluecarrot16. Autores: bluecarrot16,
  Benjamin K. Smith (BenCreating), Stephen Challener (Redshrike).
- `hat/cloth/leather_cap/adult/walk/walnut.png` — original by Johannes
  Sjölund (wulax), female by Matthew Krohn, mapped to all frames w/recolors
  by JaidynReiman. Autores: Johannes Sjölund (wulax), Matthew Krohn (Makrohn),
  JaidynReiman.
- `hat/formal/crown/adult/walk/crown_gold.png` — Autores: DarkwallLKE,
  Charles Sanchez (CharlesGabriel).
- `head/horns/curled/adult/walk.png` — Autor: Nila122. Licenças: OGA-BY 3.0,
  GPL 3.0, CC-BY-SA 3.0. Fonte: https://opengameart.org/content/lpc-lizard-headgear
- `facial/glasses/glasses/adult/walk/black.png` — Autor: ElizaWy.
- `torso/jacket/iverness/male/walk/black.png` — Autor: bluecarrot16.
- `body/wings/feathered/adult/{bg,fg}/walk/ash.png` — original by ElizaWy,
  added to most remaining frames by JaidynReiman. Autores: ElizaWy,
  Stephen Challener (Redshrike), JaidynReiman.
- `hat/pirate/tricorne/basic/adult/walk.png` — Pirate Hat by Bluecarrot16,
  layers e animações adicionadas por JaidynReiman. Autor: bluecarrot16.
- `hat/pirate/bicorne/athwart/basic/adult/walk.png` — Pirate Hat by
  Bluecarrot16, layers e animações adicionadas por JaidynReiman. Autor:
  bluecarrot16.
- `hat/cloth/bandana/adult/walk.png` — Autores: Matthew Krohn (Makrohn),
  JaidynReiman, Marcel van de Steeg (MadMarcel).
- `hat/cloth/hood/adult/walk.png` — Brown hood by Wulax, recolors mapeados
  pra idle/run/jump/combate revisado por JaidynReiman, com recolors
  adicionais. Autores: Johannes Sjölund (wulax), JaidynReiman.
- `hat/formal/bowler/adult/walk.png` — Autor: bluecarrot16.
- `hat/formal/tiara/adult/walk.png` — Autor: Luke Mehl.
- `hat/formal/tophat/adult/walk.png` — Autor: bluecarrot16.
- `hat/headband/thick/adult/walk.png` — Autor: JaidynReiman.
- `hat/helmet/barbarian_viking/adult/walk.png` — versão original por
  bluecarrot16, redução de cores por Napsio (Vitruvian Studio). Autores:
  bluecarrot16, JaidynReiman, Napsio (Vitruvian Studio).
- `hat/helmet/greathelm/male/walk.png` — Autor: bluecarrot16.
- `hat/helmet/legion/adult/walk.png` — Autores: bluecarrot16, Nila122,
  JaidynReiman, Matthew Krohn (Makrohn), Johannes Sjölund (wulax).
- `hat/holiday/christmas/adult/walk.png` — Santa/Elf Hat por bluecarrot16,
  Santa Hat sem recorte por JaidynReiman. Autores: bluecarrot16,
  JaidynReiman.
- `hat/magic/wizard/base/adult/walk.png` — chapéu de mago original e
  recolors por bigbeargames e reemax; dividido em camadas separadas com
  novos recolors por JaidynReiman. Autores: Michael Whitlock (bigbeargames),
  Tuomo Untinen (reemax), JaidynReiman.
- `neck/scarf/walk.png` — original por Nila122, animações de
  climb/sit/emote/jump/run por JaidynReiman. Autores: Nila122, JaidynReiman,
  Johannes Sjölund (wulax), Stephen Challener (Redshrike).
- `neck/tie/bowtie/adult/walk.png` — originalmente por pennomi/laetissima/
  Makrohn, editado por bluecarrot16, recolors por JaidynReiman. Autores:
  JaidynReiman, bluecarrot16, Thane Brimhall (pennomi), laetissima, Makrohn.
- `facial/glasses/sunglasses/adult/walk.png` — Autores: Michael Whitlock
  (bigbeargames), Thane Brimhall (pennomi), laetissima.
- `facial/monocle/left/adult/walk.png` — Autores: bluecarrot16,
  Thane Brimhall (pennomi), laetissima.
- `facial/patches/eyepatch/ambi/adult/walk.png` — Autor: bluecarrot16.
- `neck/necklace/female/walk/gold.png` — animações extras por bluecarrot16.
  Autores: bluecarrot16, Luke Mehl.
- `body/wings/bat/adult/{bg,fg}/walk/ash.png` — original por ElizaWy,
  adicionado à maioria dos frames restantes por JaidynReiman. Autores:
  ElizaWy, JaidynReiman.
- `body/wings/dragonfly/solid/{bg,fg}/walk/dragonfly.png` — "In dedication
  to my grandmother, Sharon Rowe". Autor: The Foreman.
- `body/wings/monarch/base/{bg,fg}/walk/monarch.png` — "In dedication to my
  grandmother, Sharon Rowe". Autor: The Foreman.

## Licença

Código sob [GPL-3.0](LICENSE). Os sprites em `web/assets/lpc/` são do Liberated
Pixel Cup, sob CC-BY-SA 3.0 / GPL 3.0 (autores listados em Créditos acima).

## Testes

`pytest` roda toda a suíte (parsing de comando, estado persistido, pontos,
áudios, sorteio, servidor web). A renderização do sprite (fatiamento de frame, composição de camadas,
recolor) não tem suíte automatizada — ver `docs/superpowers/plans/2026-08-30-lpc-pixelart-avatars.md`
pra como verificar isso manualmente. O comportamento de IRC ao vivo e a animação no
navegador só dá pra verificar manualmente: suba o app, abra a URL impressa
no navegador (ou no Browser Source do OBS) e digite os comandos no chat de
teste.
