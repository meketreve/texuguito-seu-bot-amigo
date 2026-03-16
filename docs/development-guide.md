# Development Guide - Texuguito Bot

## Prerequisites
- **Python**: Versão 3.10 ou superior instalada.
- **Twitch Developer Account**: Para criar uma aplicação e obter Client ID e Client Secret.

## Environment Setup
1. Clone o repositório.
2. Crie um ambiente virtual (opcional, mas recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration
Execute o script de configuração para gerar as credenciais necessárias:
```bash
python setup.py
```
Isso criará o arquivo `.env` com os tokens de acesso.

## Project Execution
Para rodar o bot em modo de desenvolvimento:
```bash
python bot.py
```
Ou use os scripts facilitadores:
- `run.bat`: Inicia o bot.
- `install.bat`: Reinstala dependências.

## Common Tasks
- **Adicionar Áudios**: Coloque arquivos `.mp3` em `files/audio/<valor>/`.
- **Alterar Volume**: Edite `audio_volume` no `config.json`.
