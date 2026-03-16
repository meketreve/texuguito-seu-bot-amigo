# Project Overview - Texuguito Bot

## Executive Summary
O **Texuguito Bot** é um bot de chat para streamers da Twitch, focado em interação através de áudios. Ele utiliza um sistema de pontos local para permitir que espectadores toquem sons no computador do streamer.

## Technology Stack
| Category | Technology |
| :--- | :--- |
| **Language** | Python 3.10+ |
| **Framework** | TwitchIO |
| **Audio Processing** | Pygame |
| **Data Storage** | JSON (local) |
| **External APIs** | Twitch API |

## Repository Structure
- **Type**: Monolith
- **Architecture**: Event-driven (Twitch chat events)

## Getting Started
1. Instale as dependências: `pip install -r requirements.txt`
2. Configure as credenciais: `python setup.py`
3. Execute o bot: `run.bat` ou `python bot.py`
