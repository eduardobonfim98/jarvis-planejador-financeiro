"""
Configurações globais do Jarvis.

Este arquivo centraliza todas as configurações do projeto:
- Caminhos de diretórios
- Configurações do banco de dados
- Chaves de API
- Configurações de debug e logging

Todas as variáveis podem ser sobrescritas via arquivo .env
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ============================================================================
# CARREGAMENTO DE VARIÁVEIS DE AMBIENTE
# ============================================================================

# Carrega variáveis do arquivo .env na raiz do projeto
# Se não existir, usa valores padrão ou None
load_dotenv()

# ============================================================================
# DIRETÓRIOS
# ============================================================================

# Diretório base do projeto (onde está este arquivo)
BASE_DIR = Path(__file__).parent

# Diretório para salvar gráficos gerados (não usado mais no MVP, mas mantido)
PLOTS_DIR = BASE_DIR / "plots"
PLOTS_DIR.mkdir(exist_ok=True)  # Cria o diretório se não existir

# ============================================================================
# BANCO DE DADOS
# ============================================================================

# Caminho do banco de dados SQLite
# Padrão: jarvis.db na raiz do projeto
# Pode ser sobrescrito via DATABASE_PATH no .env
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "jarvis.db"))

# ============================================================================
# APIs EXTERNAS
# ============================================================================

# Token do bot do Telegram (obrigatório)
# Obtenha em: https://t.me/BotFather
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Chave da API do Google Gemini ou Vertex AI (obrigatório para LLM)
# Gemini API direta: Obtenha em https://makersuite.google.com/app/apikey (formato: AIza...)
# Vertex AI: Use chave do Google Cloud (formato: AQ...) + configure GOOGLE_CLOUD_PROJECT
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ID do projeto Google Cloud (necessário apenas para Vertex AI)
# Se usar Vertex AI, configure este valor no .env
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")

# Modelo do Gemini a usar
# Padrão: gemini-2.5-flash (rápido e barato)
# Mais rápido: gemini-2.5-flash-lite (mais rápido e econômico, ideal para alto volume)
# Outras opções: gemini-2.0-flash-exp, gemini-1.5-pro
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ============================================================================
# CONFIGURAÇÕES DE APP
# ============================================================================

# Modo debug (mostra mais informações nos logs)
# Defina DEBUG=true no .env para ativar
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Nível de log (INFO, WARNING, ERROR, DEBUG)
# Defina LOG_LEVEL=DEBUG no .env para logs detalhados
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

