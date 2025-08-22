# 🦡 Texuguito – Seu Bot Amigo  
Um bot interativo e robusto para Twitch que responde a resgates de Channel Points com sons personalizados!

## ✨ Principais Funcionalidades

- 🎵 **Reprodução de áudio** personalizada para cada recompensa
- 🔄 **Reconexão automática** em caso de queda da conexão
- 📊 **Sistema de logging** profissional com logs coloridos
- ⚙️ **Configuração externa** via arquivo JSON (sem editar código!)
- ✅ **Validação automática** de arquivos de áudio na inicialização
- 🛡️ **Tratamento robusto de erros** para máxima estabilidade
- 📱 **Comando !status** para monitoramento em tempo real

## 📌 Passos para Configuração  

### 1️⃣ **Instalação das Dependências**
```bash
# Execute o install.bat ou manualmente:
pip install -r requirements.txt
```

### 2️⃣ **Configuração da API da Twitch**
```bash
python setup.py
```
_(Por favor, leia os prompts atentamente!)_

### 3️⃣ **Configuração de Áudios**
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

### 4️⃣ **Executar o Bot**
```bash
python bot.py
```

## 📁 Estrutura do Projeto

```
texuguito-seu-bot-amigo/
├── bot.py              # Código principal do bot (melhorado!)
├── setup.py            # Script de configuração OAuth
├── config.json         # Configurações do bot (novo!)
├── requirements.txt    # Dependências (atualizado!)
├── install.bat         # Script de instalação
├── logs/               # Pasta de logs (criada automaticamente)
├── MELHORIAS.md        # Documentação das melhorias (novo!)
└── README.md           # Este arquivo
```

## 🚀 Novidades da Versão Melhorada

### 🎯 **Para Usuários**
- ✅ **Muito mais estável** - Reconecta automaticamente se cair
- 🎵 **Volume configurável** - Ajuste o volume dos sons
- 📊 **Comando !status** - Veja se o bot está funcionando
- 🔊 **Som de fallback** - Toca um som padrão para recompensas não configuradas

### 🔧 **Para Desenvolvedores**
- 📝 **Logs profissionais** - Coloridos no console + arquivo de log
- ⚙️ **Configuração externa** - Sem precisar editar código
- 🛡️ **Tratamento de erros** - Não trava mais por pequenos problemas
- 🏗️ **Código modular** - Mais fácil de entender e modificar

## 🎮 Comandos Disponíveis

- `!status` - Mostra o status atual do bot

## 🔧 Configurações Avançadas

O arquivo `config.json` permite configurar:

- 📢 **Canal do bot**
- 🎵 **Volume dos áudios** (0.0 a 1.0)
- 🔄 **Tentativas de reconexão**
- 📝 **Nível de logging** (DEBUG, INFO, WARNING, ERROR)
- 🎯 **Prefixo dos comandos**

## 📋 Dependências

- `twitchio` - Interação com Twitch
- `pygame` - Reprodução de áudio
- `websockets` - Conexão em tempo real
- `requests` - Chamadas HTTP
- `python-dotenv` - Variáveis de ambiente
- `coloredlogs` - Logs coloridos (novo!)

## 📖 Documentação Adicional

- 📄 **[MELHORIAS.md](MELHORIAS.md)** - Detalhes técnicos das melhorias implementadas

## 🆘 Solução de Problemas

### Bot não conecta?
1. Verifique se executou `setup.py` corretamente
2. Confirme se o arquivo `.env` foi criado
3. Verifique os logs em `logs/bot.log`

### Áudio não toca?
1. Verifique se os caminhos no `config.json` estão corretos
2. Confirme se os arquivos de áudio existem
3. Use `!status` para ver quantas recompensas estão configuradas

### Bot para de funcionar?
- Agora com reconexão automática! Verifique os logs para detalhes.

## 💡 Dicas

- 🎵 Use arquivos `.mp3` ou `.wav` para melhor compatibilidade
- 📁 Organize seus áudios em pastas por categoria
- 📊 Use o comando `!status` para monitorar o bot
- 📝 Monitore os logs para debug e informações
