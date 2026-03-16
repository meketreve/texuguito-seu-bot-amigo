# Architecture - Texuguito Bot

## Executive Summary
A arquitetura do bot é baseada em eventos do chat da Twitch, utilizando a biblioteca `TwitchIO` para processar comandos e a `Pygame` para saída de áudio local.

## Architecture Pattern
- **Event-Driven**: O bot escuta eventos de chat e reage baseados em comandos pré-definidos.
- **Service Layer**: A lógica de negócio está centralizada no arquivo `bot.py`.

## Data Architecture
- **NoSQL (JSON)**: Utiliza `points.json` como um armazenamento chave-valor para o saldo de pontos dos usuários.
- **Config Management**: Utiliza `config.json` para parâmetros do sistema e `.env` para credenciais.

## API Design
O bot atua como um cliente para a API da Twitch e um listener para o chat IRC da Twitch.

## Deployment Architecture
A aplicação é projetada para rodar em ambiente Windows, emulando um executável ou rodando diretamente via Python.
