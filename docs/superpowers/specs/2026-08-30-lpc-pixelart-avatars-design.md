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

[Universal LPC Spritesheet Character Generator](https://liberatedpixelcup.github.io/Universal-LPC-Spritesheet-Character-Generator/) —
confirmado ao vivo no navegador que todos os itens necessários existem:

| Campo do avatar | Item LPC escolhido | Categoria |
| --- | --- | --- |
| corpo base | Human Male, walk cycle | Body > Body Type > Male |
| `!chapeu boné` | Leather Cap | Headwear > Hats > Caps |
| `!chapeu coroa` | Crown | Headwear > Hats > Formal |
| `!chapeu chifres` | Curled Horns | Head > Appendages |
| `!acessorio óculos` | Glasses | Headwear > Facial Accessories > Glasses |
| `!acessorio capa` | Iverness cloak | Torso > Jacket |
| `!acessorio asas` | Feathered Wings | Body > Wings |

**Licença:** CC-BY-SA 3.0 / GPL 3.0 dual license — exige crédito aos
autores. A própria ferramenta gera o texto de atribuição exato (botão
"Credits (TXT)"); esse texto vai pro README numa seção "Créditos". Sem
redistribuição do gerador em si, sem custo além de manter a atribuição.

**Exportação:** usar "ZIP: Split by item" pra cada combinação necessária —
dá cada peça (corpo, chapéu, acessório) como PNG transparente separado, na
mesma grade de frames do walk-cycle, em vez de um único PNG já composto. Se
na prática o export não separar limpo (a confirmar na implementação), o
fallback é gerar um PNG já composto por combinação (corpo+chapéu+acessório) —
mais arquivos, mesma ideia, só perde a independência de camadas.

Todos os arquivos baixados vão pra `web/assets/lpc/`, versionados no repo
(são pequenos, poucos KB cada).

## Corte de frames (walk-cycle)

LPC exporta o walk-cycle em 4 direções (up/down/left/right), várias colunas
de frame por direção. Só precisamos de **uma** direção (ex: `right`) — a
direção oposta é a mesma arte espelhada via `ctx.scale(-1, 1)` no canvas, já
que o `overlay.js` atual não distingue arte por direção, só posição. Isso
corta pela metade os frames que precisam ser carregados/fatiados.

Metadados de corte (linha/coluna da direção `right`, largura/altura de
frame, quantidade de frames do ciclo de walk) ficam num pequeno arquivo
`web/assets/lpc/manifest.json` — não hardcoded no JS, pra não quebrar se o
sprite mudar de tamanho depois.

## Cor livre (recolor em tempo real)

Só a camada de **corpo base** é tingida pela cor do `!cor` — chapéu e
acessório mantêm a cor original da arte (mesmo espírito de hoje: coroa é
sempre dourada, chifres sempre marrom, independente da cor do dono).

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
