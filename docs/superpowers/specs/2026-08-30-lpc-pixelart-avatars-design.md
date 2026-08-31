# LPC pixel-art avatars — design

Data: 2026-08-30

Supersedes the procedural pixel-grid avatar renderer described in
[2026-08-30-chat-parade-design.md](2026-08-30-chat-parade-design.md). That
spec's chat commands, persistence model, and Twitch integration are
unchanged — this document covers only how a viewer's avatar is drawn.

## Visão geral

Troca o avatar gerado por código (grid 10x13, formas geométricas simples) por
sprites reais do **Liberated Pixel Cup (LPC)**, com walk-cycle de verdade e
cor livre aplicada em tempo real via canvas (não mais "pinta a célula").
`chat_parade/avatar.py` deixa de existir; `viewer_store.py` e os comandos de
chat não mudam — `cor`/`chapeu`/`acessorio` continuam os mesmos campos,
só a interpretação deles no render muda.

## Fonte dos assets

[Universal LPC Spritesheet Character Generator](https://liberatedpixelcup.github.io/Universal-LPC-Spritesheet-Character-Generator/).
Cada peça do gerador é servida como PNG individual (transparente, já na
grade de frames do walk-cycle) numa URL própria — não precisa da UI do
gerador em produção, os arquivos já foram baixados direto por HTTP e
**já estão versionados em `web/assets/lpc/`** (commit deste spec):

| Campo do avatar | Item LPC | Arquivo local | Cor/variante |
| --- | --- | --- | --- |
| corpo base | Human Male body | `body_walk.png` | tom de pele padrão (light) |
| corpo base | Human Male head | `head_walk.png` | tom de pele padrão (light) |
| `!chapeu boné` | Leather Cap | `hat_bone_walk.png` | walnut |
| `!chapeu coroa` | Crown | `hat_coroa_walk.png` | gold |
| `!chapeu chifres` | Curled Horns | `chifres_walk.png` | tom de pele padrão (light) |
| `!acessorio óculos` | Glasses | `oculos_walk.png` | black |
| `!acessorio capa` | Iverness cloak | `capa_walk.png` | black |
| `!acessorio asas` | Feathered Wings | `asas_bg_walk.png` + `asas_fg_walk.png` | ash |

**Correção sobre o spec original:** um personagem LPC completo precisa de
**duas** camadas base, não uma — `body` (tronco/membros) e `head` (cabeça,
já com olhos) são arquivos separados que sempre se combinam. As duas levam
o tint de `!cor` juntas (compostas antes de tingir), pra não ficar com
pescoço de uma cor e corpo de outra.

**Asas têm duas camadas**, não uma: `bg` (atrás do corpo) e `fg` (na
frente) — sem isso as asas ficam por cima do personagem inteiro, errado
visualmente. Ordem de composição: `asas_bg` → corpo+cabeça tingidos →
chapéu → acessório (óculos/capa) → `asas_fg`.

**Geometria confirmada** (todos os 8 arquivos, mesma grade): 576x256px,
9 colunas x 4 linhas, célula de 64x64px. Linha da direção (`direction_row`
no manifest): 0=cima, 1=esquerda, 2=baixo, **3=direita** (a única usada —
overlay.js só anda horizontalmente, espelha pra esquerda via
`ctx.scale(-1,1)`). Colunas 1-8 são o ciclo de andar (coluna 0 é pose
parada, não usada). Tudo isso já está em `web/assets/lpc/manifest.json`.

**Licença:** CC-BY-SA 3.0 / GPL 3.0 dual license — exige crédito aos
autores. Texto de atribuição capturado do gerador (ver seção Créditos
abaixo) — falta só a de "Curled Horns" especificamente, que a task do
README deve regenerar clicando "Credits (TXT)" no gerador com a combinação
final carregada (rápido, não bloqueia o resto do plano).

## Créditos coletados (pra seção "Créditos" do README)

```
body/bodies/male/walk.png
  'Thick' Male Revised Run/Climb by JaidynReiman (based on ElizaWy's LPC Revised)
  Licenses: OGA-BY 3.0, CC-BY-SA 3.0, GPL 3.0
  Authors: bluecarrot16, JaidynReiman, Benjamin K. Smith (BenCreating), Evert,
  Eliza Wyatt (ElizaWy), TheraHedwig, MuffinElZangano, Durrani,
  Johannes Sjölund (wulax), Stephen Challener (Redshrike)

head/heads/human/male/walk.png
  original head by Redshrike, tweaks by BenCreating, modular version by bluecarrot16
  Licenses: OGA-BY 3.0, CC-BY-SA 3.0, GPL 3.0
  Authors: bluecarrot16, Benjamin K. Smith (BenCreating), Stephen Challener (Redshrike)

hat/cloth/leather_cap/adult/walk/walnut.png
  original by Johannes Sjölund (wulax), female by Matthew Krohn, mapped to all
  frames w/recolors by JaidynReiman
  Licenses: OGA-BY 3.0, CC-BY-SA 3.0, GPL 3.0
  Authors: Johannes Sjölund (wulax), Matthew Krohn (Makrohn), JaidynReiman

hat/formal/crown/adult/walk/crown_gold.png
  Licenses: CC-BY-SA 3.0, GPL 3.0
  Authors: DarkwallLKE, Charles Sanchez (CharlesGabriel)

head/horns/curled/adult/walk.png
  Créditos não capturados ainda — regenerar via "Credits (TXT)" no gerador
  com a combinação final carregada antes de publicar o README.

facial/glasses/glasses/adult/walk/black.png
  Licenses: OGA-BY 3.0
  Authors: ElizaWy

torso/jacket/iverness/male/walk/black.png
  Licenses: CC-BY-SA 3.0, GPL 3.0
  Authors: bluecarrot16

body/wings/feathered/adult/{bg,fg}/walk/ash.png
  Original by ElizaWy, added to most remaining frames by JaidynReiman
  Licenses: OGA-BY 3.0
  Authors: ElizaWy, Stephen Challener (Redshrike), JaidynReiman
```

## Corte de frames (walk-cycle)

Geometria e camadas já confirmadas acima e em `manifest.json` — nenhum
número aqui precisa ser redescoberto durante a implementação.

## Cor livre (recolor em tempo real)

Só as camadas de **corpo base** (`body` + `head`, compostas juntas primeiro)
são tingidas pela cor do `!cor` — chapéu, chifres e acessório mantêm a cor
original da arte (mesmo espírito de hoje: coroa é sempre dourada, chifres no
tom de pele padrão, independente da cor do dono).

Técnica: multiply-tint.
1. No carregamento, desenha o frame do corpo base num canvas offscreen.
2. Lê os pixels (`getImageData`), converte pra luminância (cinza) por
   pixel — isso vira uma "máscara de sombreado" reutilizável pra qualquer
   cor, gerada uma vez por frame de sprite (não por viewer).
3. Pra cada combinação única de (frame, cor hex) já vista, desenha a
   máscara + um retângulo sólido da cor com
   `ctx.globalCompositeOperation = "multiply"` num canvas próprio, cacheado
   num `Map<"frame|cor", HTMLCanvasElement>` — nunca re-tinge no mesmo
   frame/cor duas vezes.
4. `drawViewer` usa o canvas cacheado (ou tinge na hora se ainda não
   existir) em vez de desenhar pixel a pixel como hoje.

Isso preserva sombreado do sprite (multiply contra uma máscara cinza clara
aproxima bem a cor alvo) e mantém `!cor` livre (qualquer hex/nome CSS já
validado em `commands.py` — nenhuma mudança no backend de validação).

## Fluxo de dados (o que muda vs. o que não muda)

**Não muda:** `viewer_store.py` (schema do `Viewer`), `commands.py`
(parsing/validação), `twitch_chat.py`, `chatters_poller.py`, `main.py`,
persistência em `viewers.json`.

**Muda:**
- `chat_parade/avatar.py` é removido.
- `web_server.py`'s `viewer_payload` não manda mais `"grid"` (matriz de
  cores). Manda uma referência de sprite:
  ```json
  {
    "username": "...",
    "nick": "...",
    "cor": "#ff8800",
    "chapeu": "coroa",
    "acessorio": "capa",
    ...campos de status/decoração inalterados...
  }
  ```
  (o cliente já sabe montar o sprite a partir de `cor`/`chapeu`/`acessorio` —
  o server não precisa mais gerar pixel nenhum, só repassar os mesmos campos
  que já vêm do `Viewer`.)
- `web/overlay.js` ganha: carregamento de imagem (uma vez, no load),
  fatiamento de frame por tempo decorrido (walk-cycle real, não mais slide
  estático), composição de camadas (corpo tingido + chapéu + acessório),
  cache de tint por (frame, cor).
- `web/assets/lpc/*.png` + `manifest.json` novos, servidos pelo mount
  `/static` que já existe.

## Fora de escopo

- Direções verticais (up/down) do walk-cycle — o rodapé só anda
  horizontalmente, nunca precisa.
- Recolor de chapéu/acessório — mantêm cor fixa da arte original, como hoje.
- Outras animações do LPC (idle, slash, etc.) — só walk é usado.
- Fallback pixel-art desenhado à mão — não é mais necessário, todos os itens
  pedidos existem prontos no LPC.
