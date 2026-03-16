# Source Tree Analysis - Texuguito Bot

## Directory Structure
```text
texuguito-seu-bot-amigo/
├── .agent/              # Configurações do agente BMAD
├── .gemini/             # Metadados do ambiente Antigravity
├── _bmad/               # Core do BMAD (Orquestrador)
├── _bmad-output/        # Saídas geradas pelo BMAD
├── backups/             # Backups de arquivos de configuração e dados
├── build/               # Arquivos de build temporários
├── dist/                # Binários/Distribuições geradas
├── docs/                # Documentação técnica do projeto (esta pasta)
├── files/               # Ativos do bot (sons, áudios)
│   ├── audio/           # Pastas de áudio organizadas por preço (ex: 0, 100, 500)
│   └── sounds/          # Sons do sistema
├── logs/                # Histórico de execução do bot
├── .env                 # Credenciais sensíveis (ignorado pelo git)
├── bot.py               # Ponto de entrada principal da aplicação
├── bot.spec             # Configuração para geração de executável (PyInstaller)
├── config.json          # Configurações gerais (volume, reconexão)
├── points.json          # Banco de dados local de pontos dos usuários
├── requirements.txt     # Dependências Python
├── run.bat              # Script de inicialização rápida (Windows)
├── setup.bat            # Script de configuração inicial (Windows)
└── setup.py             # Script de configuração de credenciais Twitch
```

## Critical Folders
- **files/audio/**: Crucial para o funcionamento do bot, onde os streamers adicionam seus sons.
- **points.json**: Mantém o estado dos usuários (saldo de pontos).
- **bot.py**: Contém toda a lógica de processamento de comandos e conexão com a Twitch.
