# chat-parade — design

Data: 2026-08-30

## Visão geral

App em Python pra live na Twitch: um rodapé (Browser Source no OBS) mostra
avatares pixel art de quem está assistindo andando da direita pra esquerda.
Cada viewer ganha um avatar único gerado a partir do nome de usuário, e pode
personalizar cor/acessórios via comandos no chat. Também reage
automaticamente a status (sub, mod, cheer).

## Arquitetura

Processo único em `asyncio`, dois pedaços:

- **Backend (Python)** — conecta no chat da Twitch, mantém o estado de cada
  viewer, roda um servidor HTTP/WebSocket **headless** (sem abrir navegador).
- **Frontend (HTML/CSS/JS servido pelo backend)** — página com fundo
  transparente, pensada pra ser colada como Browser Source no OBS. Desenha os
  avatares em `<canvas>` e só reflete os dados que chegam por WebSocket; não
  tem lógica de estado própria.

```
Twitch IRC (chat)  ---\
                        >--> viewer_store (estado em memória + viewers.json) --> WebSocket --> overlay.html (OBS Browser Source)
Twitch Helix (chatters) --/
```

O comando `python main.py` sobe tudo: o listener de chat, o poller de
chatters e o servidor uvicorn, no mesmo loop de eventos. Ao subir, imprime no
console a URL local (ex: `http://localhost:8901/overlay`) pra colar no Browser
Source do OBS. Nenhuma janela de navegador é aberta pelo processo.

## Componentes

- `chat_parade/twitch_chat.py` — cliente `twitchio` conectado ao canal
  configurado. Escuta mensagens, reconhece comandos (`!cor`, `!chapeu`, etc),
  valida e aplica no `viewer_store`, envia confirmação/erro de volta no chat
  quando o comando falha (ex: cor inválida).
- `chat_parade/chatters_poller.py` — a cada 45s, chama o endpoint Helix `Get
  Chatters` (escopo `moderator:read:chatters`) e atualiza quem está
  presente/ausente no rodapé. Quem some da lista de chatters continua com o
  estado salvo, só para de ser desenhado.
- `chat_parade/viewer_store.py` — dono do estado: `dict[username -> Viewer]`
  em memória, com load/save em `data/viewers.json`. Salva a cada mudança
  (debounced) e no shutdown.
- `chat_parade/avatar.py` — gera o avatar determinístico: hash do username
  vira seed de um RNG (`random.Random(seed)`), que escolhe entre algumas
  variações de silhueta (corpo+cabeça) e traços (olhos, formato). A cor
  escolhida no chat pinta o corpo por cima da forma gerada. Função pura,
  testável sem rede.
- `chat_parade/commands.py` — parsing e validação dos comandos de chat
  (separado do cliente IRC pra poder testar sem conexão real).
- `chat_parade/web_server.py` — FastAPI: `GET /overlay` serve o HTML/JS/CSS
  estático; `WS /ws` manda snapshot inicial + eventos incrementais
  (`viewer_joined`, `viewer_left`, `viewer_updated`) pra qualquer client
  conectado (o overlay do OBS).
- `chat_parade/main.py` — orquestra: lê `.env`, sobe os três coroutines
  (`twitch_chat`, `chatters_poller`, `web_server`) com `asyncio.gather`.
- `web/overlay.html` + `web/overlay.js` — renderiza o canvas, mantém a lista
  de avatares e a animação de andar, escuta o WebSocket.

## Dados

`.env` (reaproveita as credenciais do projeto irmão `texuguito-seu-bot-amigo`,
que já tem o escopo `moderator:read:chatters`):

```
CLIENT_ID=...
TOKEN=...
BROADCASTER_ID=...
CHANNEL=...
```

`data/viewers.json` — um objeto por username visto:

```json
{
  "algumusuario": {
    "cor": "#ff8800",
    "chapeu": "boné",
    "acessorio": null,
    "nick": null,
    "primeira_vez": "2026-08-30T20:00:00",
    "ultima_vez": "2026-08-30T21:40:00"
  }
}
```

Campos de status (sub/mod/broadcaster, contagem de cheers recentes) **não**
são persistidos em `viewers.json` — ficam só em memória, resolvidos a partir
dos badges que vêm em cada mensagem de chat (`PRIVMSG` tags). Isso significa
que quem chega só via chatters poll (lurker que nunca falou) aparece sem
nenhuma decoração de status até mandar a primeira mensagem — não dá pra saber
se é sub/mod de alguém que nunca falou sem uma chamada extra à API por
usuário, o que não vale a pena pro efeito visual que é.

## Comandos de chat

| Comando | Quem pode | Efeito |
| --- | --- | --- |
| `!cor <nome-css ou hex>` | Todos, no próprio avatar | Troca a cor do corpo. Valida contra nomes CSS conhecidos ou regex de hex; se inválido, responde no chat com o erro. Sem cooldown. |
| `!resetcor` | Todos, no próprio avatar | Volta pra cor gerada pela seed (a "cor padrão" de cada um). |
| `!chapeu <tipo\|nenhum>` | Todos, no próprio avatar | Troca o acessório de cabeça entre um set fixo de sprites (boné, coroa, chifres, nenhum). |
| `!acessorio <tipo\|nenhum>` | Todos, no próprio avatar | Troca acessório de corpo (óculos, capa, asas, nenhum). |
| `!nick <apelido>` | Todos, no próprio avatar | Define o nome exibido no lugar do username da Twitch. Limite de 16 caracteres, filtra caracteres de controle/emoji problemáticos. |
| `!dança` | Todos, no próprio avatar | Dispara uma animação temporária (alguns segundos) no overlay, não persiste estado. |
| `!avatarmod <user> <cor>` | Mod/Broadcaster | Força a cor do avatar de outro viewer. |

Comandos desconhecidos ou malformados são ignorados silenciosamente (sem
poluir o chat com erros pra cada typo).

## Decorações automáticas (sem comando)

Resolvidas a cada mensagem a partir dos badges que a Twitch já manda:

- Sub ativo → borda dourada no avatar.
- Mod → ícone de chave inglesa acima do avatar.
- Broadcaster (você) → coroa.
- Cheer recebido → explosão de partículas por alguns segundos ao redor do
  avatar de quem deu o cheer (não persiste).

## Frontend / animação

- Avatares entram pela direita da tela e andam continuamente até saírem pela
  esquerda, dando a volta (loop) — velocidade fixa igual pra todos, sem
  configuração de comando (evita bagunça visual coordenada por chat).
  Novo viewer entra do lado direito na próxima volta.
- `!dança` sobrepõe uma animação de "pulo" por cima do ciclo de andar por
  alguns segundos e volta ao normal.
- Fundo transparente (`background: transparent` + canvas sem preenchimento),
  pra funcionar como Browser Source sem chroma key.

## Erros e resiliência

- Reconexão automática do `twitchio` em caso de queda do IRC (comportamento
  padrão da lib).
- Se o Helix `Get Chatters` falhar (rate limit, token expirado), o poller
  loga o erro e mantém o último snapshot conhecido até a próxima tentativa
  funcionar — o rodapé não esvazia por causa de uma falha passageira.
- Se o WebSocket cair (ex: OBS recarrega a fonte), o overlay reconecta
  sozinho e pede um snapshot novo.

## Testes

- Unitários (`pytest`): geração de avatar é determinística (mesma seed →
  mesmo resultado); parsing/validação de comandos (`commands.py`) cobrindo
  cor válida/inválida, nick com caracteres proibidos, permissão de
  `!avatarmod`.
- Manual: rodar `python main.py`, conferir no console a URL impressa, colar
  como Browser Source no OBS, digitar os comandos no chat de teste e
  verificar visualmente a atualização do rodapé.

## Fora de escopo (v1)

- Multiplataforma (YouTube/Kick) — só Twitch por enquanto.
- Painel web de administração (tudo é feito via comando de chat ou editando
  `viewers.json` na mão).
- Upload de imagem custom pelo viewer.
- Cooldown/rate-limit nos comandos (decisão explícita do usuário: sem
  cooldown na v1).
