# Texuguito Bot - Seu Bot Amigo

Bot para Twitch que permite espectadores tocarem áudios usando pontos locais.

## Como Funciona

- Espectadores ganham **1 ponto por minuto** ativos no chat (presentes em 2 checks seguidos de 60s)
- Usam pontos para tocar áudios (`!p <nome>`) ou TTS (`!tts <msg>`)
- Broadcaster pode sorteios de pontos (`!sorteio`)

---

## Configuração

### Requisitos

- Python 3.10+
- `pip install -r requirements.txt`

### Credenciais

Crie um App no [Twitch Dev Console](https://dev.twitch.tv/console/apps) com Redirect URI `http://localhost:3000`.

Execute `python setup.py` para gerar o `.env` com as credenciais.

### Áudios

Coloque arquivos `.mp3/.wav/.ogg` em subpastas numeradas dentro de `files/`:

```
files/
  20/    → áudios que custam 20 pts
  100/   → áudios que custam 100 pts
  200/   → áudios que custam 200 pts
  500/   → áudios que custam 500 pts
```

---

## Comandos do Chat

| Comando | Aliases | Quem pode usar | Descrição |
| :--- | :--- | :--- | :--- |
| `!pontos` | `!pts` | Todos | Mostra seu saldo de pontos |
| `!p <nome>` | `!play` | Todos | Toca um áudio (ex: `!p oof`) |
| `!tts <msg>` | - | Todos | Text-to-speech (custa 200 pts) |
| `!audios` | `!sons`, `!sounds` | Todos | Lista áudios disponíveis por preço |
| `!stop` | - | Todos | Para o áudio atual |
| `!status` | - | Todos | Status do bot |
| `!ping` | - | Todos | Verifica se bot está online |
| `!comandos` | `!help`, `!ajuda` | Todos | Lista de comandos |
| `!join` | - | Todos | Entra em sorteio ativo |
| `!reload` | - | Mod/Broadcaster | Recarrega lista de áudios |
| `!addpoints <@user> <qtd>` | `!dar`, `!give` | Mod/Broadcaster | Adiciona pontos a um usuário |
| `!sorteio <pts> <min>` | - | Broadcaster | Inicia sorteio de pontos |

---

## Configurações (config.json)

| Chave | Descrição |
| :--- | :--- |
| `audio_volume` | Volume global (0.0 a 1.0) |
| `max_reconnect_attempts` | Tentativas de reconexão ao chat |

---

## Executar

```bash
# Desenvolvimento
python bot.py

# Instalar dependências
install.bat

# Setup credenciais
setup.bat
```
