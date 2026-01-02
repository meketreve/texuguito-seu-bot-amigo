# 🦡 Texuguito – Seu Bot Amigo  
Um bot interativo e robusto para Twitch que reproduz áudios personalizados!

## 🎮 Modos de Uso

O Texuguito oferece **dois modos de funcionamento**:

### 🎤 Modo 1: Comandos no Chat (Gratuito)
Qualquer pessoa no chat pode tocar sons usando comandos!

| Comando | Descrição |
|---------|-----------|
| `!p <nome>` | Toca um áudio pelo nome |
| `!audios` | Lista todos os áudios disponíveis |
| `!stop` | Para o áudio atual |
| `!ping` | Verifica se o bot está online |
| `!comandos` | Mostra lista de comandos |
| `!reload` | Recarrega a lista de áudios |

**Como funciona:** Os áudios são organizados por custo em pastas dentro de `files/`. Exemplo:
```
files/
├── 10/       (áudios de 10 pontos)
│   └── oof.mp3
├── 50/       (áudios de 50 pontos)
│   └── epic.mp3
└── 100/      (áudios de 100 pontos)
    └── victory.mp3
```

---

### 🎁 Modo 2: Pontos de Canal (Channel Points)
Espectadores usam seus pontos de canal para resgatar recompensas com sons!

**Vantagens:**
- ✅ Custo em pontos para cada som
- ✅ Controle de quem pode usar
- ✅ Integração nativa com a Twitch
- ✅ Som de fallback para recompensas não configuradas

**Como configurar:**
1. Crie recompensas na Twitch ou use `manage.bat`
2. Configure no `config.json`:
```json
{
  "recompensas_audio": {
    "Nome da Recompensa": "files/audio/som.mp3"
  }
}
```

> ⚠️ O nome deve ser **exatamente igual** ao configurado na Twitch!

---

## ✨ Principais Funcionalidades

- 🎵 **Reprodução de áudio** personalizada
- 🔄 **Reconexão automática** em caso de queda
- 📊 **Sistema de logging** profissional com logs coloridos
- ⚙️ **Configuração externa** via arquivo JSON
- ✅ **Validação automática** de arquivos de áudio
- 🛡️ **Tratamento robusto de erros**
- 🎆 **Gerenciamento programático** de recompensas via CLI
- 🔊 **Som de fallback** para recompensas não configuradas
- 💾 **Backup automático** antes de alterações

---

## 🚀 Instalação Rápida

### ⚠️ **PRIMEIRO PASSO OBRIGATÓRIO:**
🔗 **[📖 TUTORIAL: Como Criar Seu Aplicativo Twitch](TUTORIAL_CRIAR_APP_TWITCH.md)**

### 1️⃣ Instalação das Dependências
```bash
install.bat
# ou manualmente: pip install -r requirements.txt
```

### 2️⃣ Configuração da API
```bash
python setup.py
```

### 3️⃣ Executar o Bot
```bash
run.bat
# ou: python bot.py
```

---

## 📁 Estrutura do Projeto

```
texuguito-seu-bot-amigo/
├── bot.py                 # Código principal do bot
├── setup.py               # Script de configuração OAuth
├── manage_rewards.py      # Gerenciador de recompensas
├── manage.bat             # Interface para gerenciar recompensas
├── config.json            # Configurações do bot
├── .env                   # Credenciais (não compartilhe!)
├── run.bat / install.bat  # Scripts de execução
├── logs/                  # Pasta de logs
├── backups/               # Backups do config.json
└── files/                 # Seus arquivos de áudio
```

---

## 🎆 Gerenciamento de Recompensas

Use `manage.bat` ou linha de comando:

```bash
# Listar recompensas
python manage_rewards.py list

# Criar nova recompensa
python manage_rewards.py create "Nome" --cost 100 --audio "files/som.mp3"

# Remover recompensa
python manage_rewards.py remove "Nome"

# Sincronizar com Twitch
python manage_rewards.py sync
```

---

## 🔧 Configurações Avançadas

O arquivo `config.json` permite configurar:
- 📢 **Canal do bot**
- 🎵 **Volume dos áudios** (0.0 a 1.0)
- 🔄 **Tentativas de reconexão**
- 📝 **Nível de logging** (DEBUG, INFO, WARNING, ERROR)
- 🔊 **Som de fallback** para recompensas sem áudio

---

## 🆘 Solução de Problemas

| Problema | Solução |
|----------|---------|
| Bot não conecta | Execute `setup.py` e verifique `.env` |
| Áudio não toca | Verifique caminhos no `config.json` |
| Comando não funciona | Use `!reload` para recarregar áudios |

---

## 📖 Documentação Adicional

- 📄 **[MELHORIAS.md](MELHORIAS.md)** - Detalhes técnicos
- 🎁 **[GERENCIAMENTO_RECOMPENSAS.md](GERENCIAMENTO_RECOMPENSAS.md)** - Guia de recompensas
- 📺 **[TUTORIAL_CRIAR_APP_TWITCH.md](TUTORIAL_CRIAR_APP_TWITCH.md)** - Criar app Twitch

---

🎯 **Feito com carinho!** 🦡
