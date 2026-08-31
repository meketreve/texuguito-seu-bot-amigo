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
| `!cor <nome ou hex>` | Todos, no próprio avatar | Troca a cor do corpo. |
| `!resetcor` | Todos, no próprio avatar | Volta pra cor gerada pela seed. |
| `!chapeu <boné\|coroa\|chifres\|nenhum>` | Todos, no próprio avatar | Troca o chapéu. |
| `!acessorio <óculos\|capa\|asas\|nenhum>` | Todos, no próprio avatar | Troca o acessório. |
| `!nick <apelido>` | Todos, no próprio avatar | Nome exibido no rodapé. |
| `!dança` (ou `!danca`) | Todos, no próprio avatar | Dispara uma animação por alguns segundos. |
| `!avatarmod <usuario> <cor>` | Mod/Broadcaster | Força a cor do avatar de outro viewer. |

Decorações automáticas (sem comando): sub ativo ganha borda dourada, mod
ganha a etiqueta "MOD", broadcaster ganha uma coroa (♛), e dar cheer solta um
anel dourado ao redor do avatar por alguns segundos.

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

## Testes

`pytest` roda toda a suíte (parsing de comando, estado persistido, servidor
web). A renderização do sprite (fatiamento de frame, composição de camadas,
recolor) não tem suíte automatizada — ver `docs/superpowers/plans/2026-08-30-lpc-pixelart-avatars.md`
pra como verificar isso manualmente. O comportamento de IRC ao vivo e a animação no
navegador só dá pra verificar manualmente: suba o app, abra a URL impressa
no navegador (ou no Browser Source do OBS) e digite os comandos no chat de
teste.
