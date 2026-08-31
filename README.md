# chat-parade

Overlay pixel art pra live na Twitch: todo mundo assistindo aparece andando
no rodapé da stream, com avatar gerado automaticamente e personalizável via
comandos no chat.

## Setup

1. `pip install -r requirements.txt`
2. Copie `.env.example` pra `.env` e preencha com as credenciais do seu app
   Twitch (pode reaproveitar as mesmas do `texuguito-seu-bot-amigo`, que já
   tem o escopo `moderator:read:chatters`):

   ```
   CLIENT_ID=...
   TOKEN=...
   BROADCASTER_ID=...
   CHANNEL=...
   ```

3. Rode os testes: `pytest`
4. Suba o app: `python -m chat_parade.main`

O processo não abre navegador nenhum — ele imprime no console algo como:

```
[chat-parade] overlay pronto em: http://localhost:8901/overlay
[chat-parade] cole essa URL como Browser Source no OBS.
```

Cole essa URL num Browser Source do OBS (largura/altura à sua escolha, fundo
já é transparente).

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

## Se o token expirar

O token é o mesmo app do `texuguito-seu-bot-amigo` — rode `python setup.py`
naquele projeto de novo pra gerar um token novo e copie os valores pro `.env`
daqui.

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

## Testes

`pytest` roda toda a suíte (parsing de comando, estado persistido, servidor
web). A renderização do sprite (fatiamento de frame, composição de camadas,
recolor) não tem suíte automatizada — ver `docs/superpowers/plans/2026-08-30-lpc-pixelart-avatars.md`
pra como verificar isso manualmente. O comportamento de IRC ao vivo e a animação no
navegador só dá pra verificar manualmente: suba o app, abra a URL impressa
no navegador (ou no Browser Source do OBS) e digite os comandos no chat de
teste.
