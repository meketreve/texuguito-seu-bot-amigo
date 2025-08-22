# 🦡 Texuguito – Seu Bot Amigo  
Um bot interativo e robusto para Twitch que responde a resgates de Channel Points com sons personalizados!

## ✨ Principais Funcionalidades

- 🎵 **Reprodução de áudio** personalizada para cada recompensa
- 🔄 **Reconexão automática** em caso de queda da conexão
- 📊 **Sistema de logging** profissional com logs coloridos
- ⚙️ **Configuração externa** via arquivo JSON (sem editar código!)
- ✅ **Validação automática** de arquivos de áudio na inicialização
- 🛡️ **Tratamento robusto de erros** para máxima estabilidade
- 🎆 **Gerenciamento programático** de recompensas via CLI
- 🔄 **Sincronização automática** entre Twitch e configuração local
- 💾 **Backup automático** antes de qualquer alteração

## 📌 Passos para Configuração  

### ⚠️ **PRIMEIRO PASSO OBRIGATÓRIO:**
🔗 **[📖 TUTORIAL: Como Criar Seu Aplicativo Twitch](TUTORIAL_CRIAR_APP_TWITCH.md)**

**🚨 IMPORTANTE:** Cada usuário deve ter seu próprio aplicativo registrado na Twitch!

---

### 1️⃣ **Instalação das Dependências**
```bash
# Execute o install.bat ou manualmente:
pip install -r requirements.txt
```

### 2️⃣ **Criar Aplicativo Twitch (OBRIGATÓRIO)**
1. Siga o **[Tutorial Completo](TUTORIAL_CRIAR_APP_TWITCH.md)**
2. Anote seu Client ID

### 3️⃣ **Configuração da API da Twitch**
```bash
python setup.py
```
_(Cole o Client ID do passo anterior quando solicitado)_

### 4️⃣ **Configuração de Áudios**
- Edite o arquivo `config.json` criado
- Configure os caminhos dos arquivos de áudio para cada recompensa
- Organize seus áudios na pasta `files/`

**Exemplo de configuração:**
```json
{
  "recompensas_audio": {
    "nome_da_recompensa": "files/audio/meu_som.mp3",
    "outra_recompensa": "files/sons/outro_som.wav"
  }
}
```

### 5️⃣ **Executar o Bot**
```bash
python bot.py
```

## 📁 Estrutura do Projeto

```
texuguito-seu-bot-amigo/
├── bot.py                          # Código principal do bot (melhorado!)
├── setup.py                        # Script de configuração OAuth
├── manage_rewards.py               # Gerenciador de recompensas (novo!)
├── exemplo_uso.py                  # Exemplo de uso do sistema (novo!)
├── config.json                     # Configurações do bot (novo!)
├── requirements.txt                # Dependências (atualizado!)
├── install.bat                     # Script de instalação
├── .env                            # Credenciais da Twitch (gerado pelo setup.py)
├── .gitignore                      # Arquivos ignorados pelo Git
├── logs/                           # Pasta de logs (criada automaticamente)
│   └── bot.log                     # Log do bot
├── backups/                        # Backups do config.json (novo!)
│   └── config_backup_*.json        # Backups com timestamp
├── files/                          # Seus arquivos de áudio
│   ├── audio/                      # Sons básicos
│   ├── epic/                       # Sons épicos
│   ├── funny/                      # Sons engraçados
│   └── victory/                    # Sons de vitória
├── MELHORIAS.md                    # Documentação das melhorias (novo!)
├── GERENCIAMENTO_RECOMPENSAS.md    # Guia do sistema de recompensas (novo!)
├── TUTORIAL_CRIAR_APP_TWITCH.md    # Tutorial para criar aplicativo Twitch (novo!)
└── README.md                       # Este arquivo
```

## 🚀 Novidades da Versão Melhorada

### 🎯 **Para Usuários**
- ✅ **Muito mais estável** - Reconecta automaticamente se cair
- 🎵 **Volume configurável** - Ajuste o volume dos sons
- 📊 **Monitoramento via logs** - Acompanhe o funcionamento
- 🔊 **Som de fallback** - Toca um som padrão para recompensas não configuradas

### 🔧 **Para Desenvolvedores**
- 📝 **Logs profissionais** - Coloridos no console + arquivo de log
- ⚙️ **Configuração externa** - Sem precisar editar código
- 🛡️ **Tratamento de erros** - Não trava mais por pequenos problemas
- 🏗️ **Código modular** - Mais fácil de entender e modificar

## 🔧 Configurações Avançadas

O arquivo `config.json` permite configurar:

- 📢 **Canal do bot**
- 🎵 **Volume dos áudios** (0.0 a 1.0)
- 🔄 **Tentativas de reconexão**
- 📝 **Nível de logging** (DEBUG, INFO, WARNING, ERROR)

## 📋 Dependências

- `twitchio` - Interação com Twitch
- `pygame` - Reprodução de áudio
- `websockets` - Conexão em tempo real
- `requests` - Chamadas HTTP
- `python-dotenv` - Variáveis de ambiente
- `coloredlogs` - Logs coloridos (novo!)

## 🞆 Gerenciamento Programático de Recompensas

O bot agora inclui um sistema completo para gerenciar recompensas:

### 💻 Via Linha de Comando
```bash
# Listar recompensas
python manage_rewards.py list

# Criar nova recompensa
python manage_rewards.py create "Nome" --cost 100 --audio "files/som.mp3"

# Remover recompensa
python manage_rewards.py remove "Nome"

# Sincronizar e detectar problemas
python manage_rewards.py sync
```

### 🎆 Recursos Avançados
- 💾 **Backup automático** do config antes de alterações
- 🔍 **Validação de arquivos** antes de criar recompensas
- 🔄 **Sincronização** entre Twitch e arquivo local
- 🛡️ **Sistema de validação** robusto
- 📊 **Detecção de inconsistências** automática

## 📖 Documentação Adicional

- 📄 **[MELHORIAS.md](MELHORIAS.md)** - Detalhes técnicos das melhorias implementadas
- 🎁 **[GERENCIAMENTO_RECOMPENSAS.md](GERENCIAMENTO_RECOMPENSAS.md)** - Guia completo do sistema de recompensas
- 📝 **[exemplo_uso.py](exemplo_uso.py)** - Script de demonstração do sistema

## 🆘 Solução de Problemas

### Bot não conecta?
1. Verifique se executou `setup.py` corretamente
2. Confirme se o arquivo `.env` foi criado
3. Verifique os logs em `logs/bot.log`

### Áudio não toca?
1. Verifique se os caminhos no `config.json` estão corretos
2. Confirme se os arquivos de áudio existem
3. Consulte os logs em `logs/bot.log` para detalhes

### Bot para de funcionar?
- Agora com reconexão automática! Verifique os logs para detalhes.

## 💡 Dicas

- 🎵 Use arquivos `.mp3` ou `.wav` para melhor compatibilidade
- 📁 Organize seus áudios em pastas por categoria
- 📊 Monitore os logs para acompanhar o funcionamento
- 📝 Monitore os logs para debug e informações
