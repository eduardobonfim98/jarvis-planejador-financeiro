# Jarvis – Assistente Financeiro

Bot do Telegram com inteligência artificial (Gemini) para registrar e analisar gastos.

## ⚙️ Ambiente com UV

1. [Instale o UV](https://github.com/astral-sh/uv#installation) (se ainda não tiver).
2. Na raiz do projeto, crie/atualize o ambiente:
   ```bash
   uv sync
   ```
   Isso cria `.venv/` e instala as dependências do `pyproject.toml`.
3. Ative o ambiente quando precisar (opcional):
   ```bash
   source .venv/bin/activate  # macOS/Linux
   .venv\Scripts\activate     # Windows PowerShell
   ```

## 🔐 Variáveis de ambiente

Crie um arquivo `.env` baseado nas chaves que você já possui:

```
TELEGRAM_BOT_TOKEN=xxx
GEMINI_API_KEY=yyy
# GEMINI_MODEL=gemini-1.5-flash-latest  # opcional
```

O `.env` já está no `.gitignore` para evitar leaks.

## ▶️ Rodando o bot

```bash
uv run python bot.py
```

O comando `uv run` garante que o script use o ambiente sincronizado.

## 📦 Dependências principais

- `python-telegram-bot`
- `python-dotenv`
- `google-generativeai`

Tudo é resolvido por `uv`. Para adicionar novas libs:

```bash
uv add nome-da-lib
uv sync
```

## ✅ Próximos passos

- Implementar persistência (SQLite).
- Criar agents/tools descritos em `Projeto.md`.
- Adicionar testes automatizados e linting conforme evoluir.

