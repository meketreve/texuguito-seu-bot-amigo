# 🦡 Texuguito Bot - Seu Bot Amigo 🎵

O **Texuguito Bot** é uma aplicação para streamers da Twitch que permite aos espectadores dispararem áudios no seu computador usando um sistema de pontos local baseado na atividade no chat.

## 🚀 Como Funciona

1.  **Ganhe Pontos**: Fique no chat e interaja! A cada 5 minutos, o bot verifica quem está presente. Se você estiver lá por dois ciclos seguidos, ganha **50 pontos**.
2.  **Toque Áudios**: Use o comando `!p <nome>` para tocar um áudio. Cada áudio tem um custo baseado na pasta onde ele está localizado.
3.  **Comandos principais**:
    *   `!pontos`: Veja seu saldo de pontos.
    *   `!p <nome>`: Toca o áudio se você tiver saldo.
    *   `!audios`: Lista os sons disponíveis e seus preços.

---

## 🛠️ Configuração Inicial

### 1. Requisitos
*   Python 3.10 ou superior.
*   Bibliotecas: `pip install -r requirements.txt`

### 2. Credenciais da Twitch
Você precisará de um App no [Twitch Dev Console](https://dev.twitch.tv/console/apps).
1.  Redirect URI: `http://localhost:3000`
2.  Execute `python setup.py` e siga as instruções para gerar seu `.env`.

### 3. Organização dos Áudios
Coloque seus arquivos `.mp3` na pasta `files/`. Use pastas numeradas para definir o preço:
*   `files/100/` -> Áudios que custam 100 pontos.
*   `files/500/` -> Áudios que custam 500 pontos.
*   `files/0/`   -> Áudios gratuitos.

---

## 📋 Comandos do Chat

| Comando | Aliases | Descrição |
| :--- | :--- | :--- |
| `!pontos` | `!pts`, `!saldo` | Mostra seu saldo de pontos locais |
| `!p <nome>` | `!play` | Toca um áudio (ex: `!p oof`) |
| `!audios` | `!sons` | Lista os áudios disponíveis por categoria de preço |
| `!stop` | `!parar` | Para o áudio que está tocando no momento |
| `!reload` | - | Recarrega a lista de áudios (apenas streamer/mods) |
| `!comandos` | `!help` | Mostra a lista de comandos |

---

## ⚙️ Configurações (config.json)

*   `audio_volume`: Volume global (0.0 a 1.0).
*   `max_reconnect_attempts`: Tentativas de conexão com o chat.
*   `fallback_sound`: Som tocado quando ocorre um erro.

---

## 📜 Notas de Versão
Esta versão utiliza um **sistema de pontos local** salvo em `points.json`, independente dos Pontos de Canal da Twitch. Isso permite maior flexibilidade e automação para todos os integrantes do chat.

Bom streaming! 🦡
