# 🎁 Sistema de Gerenciamento de Recompensas

O Texuguito Bot agora possui um sistema completo para gerenciar recompensas de Channel Points da Twitch de forma programática, sincronizando automaticamente entre a plataforma e o arquivo de configuração local.

## 📋 Visão Geral

Este sistema permite:
- ✅ **Criar recompensas** diretamente via linha de comando ou bot
- 📝 **Listar** todas as recompensas configuradas
- 🗑️ **Remover** recompensas da Twitch e config
- 🔄 **Sincronizar** entre Twitch e arquivo local
- ⚡ **Gerenciar pelo chat** usando comandos do bot
- 💾 **Backup automático** antes de qualquer alteração

## 🛠️ Como Usar

### 1. 📋 Via Linha de Comando (`manage_rewards.py`)

#### Listar Recompensas Existentes
```bash
python manage_rewards.py list
```

#### Criar Nova Recompensa
```bash
python manage_rewards.py create "Nome da Recompensa" --cost 100 --audio "files/audio/som.mp3"
```

**Opções avançadas:**
```bash
python manage_rewards.py create "Som Epic" \
    --cost 500 \
    --audio "files/epic/epic_sound.mp3" \
    --prompt "Um som épico para momentos especiais!" \
    --color "#FF0000" \
    --max-stream 5 \
    --max-user 1 \
    --cooldown 60
```

#### Remover Recompensa
```bash
python manage_rewards.py remove "Nome da Recompensa"
```

#### Sincronizar e Detectar Problemas
```bash
python manage_rewards.py sync
```

### 2. 💬 Via Chat do Bot (Comandos)

#### Verificar Status
```
!status
```

#### Listar Recompensas
```
!list_rewards
```
*Apenas para administradores (broadcaster/mods)*

#### Adicionar Recompensa
```
!add_reward "Nome da Recompensa" 100 "files/audio/som.mp3"
```
*Apenas para administradores*

#### Remover Recompensa
```
!remove_reward "Nome da Recompensa"
```
*Apenas para administradores*

#### Sincronizar
```
!sync_rewards
```
*Apenas para administradores*

## 📁 Estrutura de Arquivos

```
texuguito-seu-bot-amigo/
├── manage_rewards.py       # Script de gerenciamento
├── bot.py                  # Bot principal (com comandos admin)
├── config.json            # Configurações das recompensas
├── backups/               # Backups automáticos do config
│   ├── config_backup_20250822_074500.json
│   └── config_backup_20250822_080000.json
├── logs/                  # Logs detalhados
│   └── bot.log
└── files/                 # Seus arquivos de áudio
    ├── audio/
    ├── epic/
    └── sounds/
```

## 🔧 Configurações Avançadas

### Opções de Recompensa

Ao criar recompensas, você pode configurar:

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `--cost` | int | Custo em pontos (obrigatório) |
| `--audio` | str | Caminho do arquivo de áudio (obrigatório) |
| `--prompt` | str | Descrição da recompensa |
| `--color` | str | Cor de fundo (hex, ex: #FF0000) |
| `--max-stream` | int | Máximo de resgates por stream |
| `--max-user` | int | Máximo por usuário por stream |
| `--cooldown` | int | Cooldown global em segundos |

### Exemplo Completo
```bash
python manage_rewards.py create "Som de Vitória" \
    --cost 200 \
    --audio "files/victory/victory_sound.mp3" \
    --prompt "Toca quando algo épico acontece!" \
    --color "#FFD700" \
    --max-stream 10 \
    --max-user 2 \
    --cooldown 30
```

## 🚨 Sistema de Segurança

### Backups Automáticos
- 💾 **Backup antes de cada alteração** no config.json
- 📅 **Nome com timestamp** para fácil identificação
- 🗂️ **Pasta dedicada** `backups/` 
- ♻️ **Restauração fácil** em caso de problemas

### Permissões de Comandos
- 🔐 **Apenas admins** podem usar comandos de gerenciamento
- ✅ **Broadcaster** sempre tem acesso
- 👮‍♂️ **Moderadores** têm acesso aos comandos
- 🚫 **Usuários normais** só podem ver status

### Validações
- ✅ **Arquivo de áudio existe** antes de criar
- 🔍 **Custo é um número válido**
- 📝 **Nome da recompensa não vazio**
- 🔄 **Credenciais da Twitch configuradas**

## 📊 Sincronização e Diagnóstico

### Comando `sync`
Detecta e reporta:
- 🔍 **Recompensas órfãs** (só na Twitch, não no config)
- ⚠️ **Recompensas perdidas** (só no config, não na Twitch)
- ❌ **Arquivos de áudio faltando**

### Exemplo de Output
```
🔄 Sincronizando recompensas...

⚠️  Encontradas 2 recompensas órfãs (apenas na Twitch):
   - Som Teste 1
   - Som Teste 2
💡 Use 'remove' para excluir da Twitch ou configure manualmente o áudio

❌ Encontrados 1 arquivos de áudio faltando:
   - Som Epic: files/epic/missing_sound.mp3

⚠️  Encontradas 1 recompensas perdidas (apenas no config):
   - Som Antigo
💡 Essas recompensas podem ter sido removidas manualmente da Twitch
```

## 📝 Exemplo de Workflow Completo

### 1. Setup Inicial
```bash
# Primeiro, configure as credenciais
python setup.py

# Instale dependências
pip install -r requirements.txt
```

### 2. Organizando Áudios
```bash
# Crie estrutura de pastas
mkdir -p files/audio files/epic files/funny files/victory

# Coloque seus arquivos .mp3/.wav nas pastas
```

### 3. Adicionando Recompensas
```bash
# Som básico
python manage_rewards.py create "Oof" --cost 50 --audio "files/audio/oof.mp3"

# Som épico com limitações
python manage_rewards.py create "Som Épico" \
    --cost 500 \
    --audio "files/epic/epic.mp3" \
    --prompt "Para momentos épicos!" \
    --max-stream 3 \
    --cooldown 120

# Som engraçado
python manage_rewards.py create "Risada" \
    --cost 100 \
    --audio "files/funny/laugh.mp3" \
    --color "#FF69B4"
```

### 4. Verificando Status
```bash
# Lista todas as recompensas
python manage_rewards.py list

# Verifica inconsistências
python manage_rewards.py sync
```

### 5. Executando o Bot
```bash
python bot.py
```

### 6. Gerenciando pelo Chat
```
!status                                    # Verifica se está funcionando
!list_rewards                             # Lista recompensas (admin only)
!add_reward "Novo Som" 150 "files/new.mp3"  # Adiciona (admin only)
```

## 🎯 Dicas e Melhores Práticas

### Organização de Arquivos
- 📁 **Use pastas por categoria**: `victory/`, `funny/`, `epic/`
- 🏷️ **Nomes descritivos**: `epic_victory.mp3`, `funny_laugh.wav`
- 📏 **Tamanhos moderados**: Evite arquivos muito longos (>10s)

### Custos de Recompensas
- 💰 **50-100 pontos**: Sons básicos/comuns
- 💎 **200-500 pontos**: Sons especiais
- 👑 **500+ pontos**: Sons épicos/raros

### Limitações Inteligentes
- 🔄 **Cooldowns**: Evite spam de sons
- 📊 **Max por stream**: Controle uso excessivo
- 👤 **Max por usuário**: Evite dominação

### Monitoramento
- 📋 **`!list_rewards`** regularmente para verificar
- 🔄 **`!sync_rewards`** após mudanças manuais
- 📝 **Monitore logs** para problemas

## 🚨 Solução de Problemas

### Erro: "Credenciais não configuradas"
```bash
# Execute o setup novamente
python setup.py
```

### Erro: "Arquivo de áudio não encontrado"
- ✅ Verifique se o caminho está correto
- 📁 Certifique-se de que o arquivo existe
- 🔄 Use caminhos relativos: `files/audio/som.mp3`

### Recompensa não aparece no bot
```bash
# Sincronize manualmente
python manage_rewards.py sync

# Reinicie o bot
```

### Problemas de permissão no chat
- ✅ Verifique se você é broadcaster ou mod
- 🔄 Teste com `!status` primeiro
- 📝 Verifique logs para erros

### Backup Recovery
```bash
# Para restaurar um backup
cp backups/config_backup_TIMESTAMP.json config.json

# Reinicie o bot
python bot.py
```

## 🎉 Conclusão

Com este sistema, você pode:
- ⚡ **Gerenciar recompensas rapidamente** via CLI ou chat
- 🔄 **Manter tudo sincronizado** automaticamente
- 💾 **Backups seguros** para evitar perdas
- 📊 **Monitoramento completo** de inconsistências
- 🎯 **Controle total** sobre a experiência dos viewers

O gerenciamento de recompensas agora é muito mais profissional e eficiente! 🚀
