"""
Bot do Telegram - Jarvis

Este é o arquivo principal que inicia o bot do Telegram.
Ele recebe mensagens dos usuários e as processa através do workflow LangGraph.

Fluxo:
1. Usuário envia mensagem no Telegram
2. Bot recebe e chama handle_message()
3. handle_message() executa o workflow LangGraph
4. Workflow processa através dos agentes (Partner → Finance/Setup → Output)
5. Resposta final é enviada de volta ao usuário

Para debug:
- Logs aparecem no console com timestamp e nome do agente
- Erros são capturados e mensagem genérica é enviada ao usuário
- Use print() ou self.log() nos agentes para debug
"""

import asyncio
import os
from functools import partial

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from database import init_database
from graph.workflow import run_workflow
import re

# ============================================================================
# CONFIGURAÇÃO INICIAL
# ============================================================================

# Carrega variáveis de ambiente do arquivo .env
# IMPORTANTE: Crie um arquivo .env na raiz com:
#   TELEGRAM_BOT_TOKEN=seu_token_aqui
#   GEMINI_API_KEY=sua_chave_aqui (Gemini API ou Vertex AI)
#   GOOGLE_CLOUD_PROJECT=seu-project-id (apenas para Vertex AI)
load_dotenv()

# Tokens e configurações
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Validação: Bot não funciona sem token do Telegram
if not BOT_TOKEN:
    raise ValueError("⚠️ TELEGRAM_BOT_TOKEN não encontrado! Crie um arquivo .env com seu token.")

# O LLM é configurado automaticamente pelos agentes usando llm_client.py
# Não precisa configurar aqui - cada agente inicializa seu próprio cliente LLM


def escape_markdown_v2(text: str) -> str:
    """
    Escapa caracteres especiais do MarkdownV2 do Telegram.
    
    Caracteres que precisam ser escapados: _ * [ ] ( ) ~ ` > # + - = | { } . !
    """
    # Lista de caracteres especiais do MarkdownV2
    special_chars = r'_*[]()~`>#+-=|{}.!'
    # Escapa cada caractere especial
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def safe_markdown(text: str) -> str:
    """
    Tenta tornar o texto seguro para Markdown, removendo formatação problemática.
    
    Se houver muitos caracteres especiais, remove a formatação Markdown.
    """
    # Conta quantos caracteres de formatação Markdown existem
    markdown_chars = text.count('*') + text.count('_') + text.count('`')
    
    # Se houver muitos caracteres de formatação, pode ser problemático
    # Remove formatação Markdown básica mas mantém o conteúdo
    if markdown_chars > 20:  # Limite arbitrário
        # Remove apenas os caracteres de formatação, mantendo o texto
        text = re.sub(r'\*([^*]+)\*', r'\1', text)  # Remove *texto*
        text = re.sub(r'_([^_]+)_', r'\1', text)    # Remove _texto_
        text = text.replace('`', '')                 # Remove `
    
    return text


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler para o comando /start do Telegram.
    
    Quando o usuário envia /start, esta função é chamada e envia uma mensagem
    de boas-vindas explicando o que o bot faz.
    
    Args:
        update: Objeto Update do Telegram com informações da mensagem
        context: Contexto do bot (não usado aqui, mas necessário pela API)
    """
    await update.message.reply_text(
        "Oi! 👋 Eu sou o Jarvis, seu assistente financeiro!\n\n"
        "Posso ajudar você a:\n"
        "• Registrar seus gastos\n"
        "• Consultar seus gastos por categoria\n"
        "• Gerar gráficos e relatórios\n"
        "• Alertar sobre limites de gasto\n\n"
        "Envie qualquer mensagem para começar!"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler principal para todas as mensagens de texto do Telegram.
    
    Esta função é chamada sempre que o usuário envia uma mensagem (exceto /start).
    Ela processa a mensagem através do workflow LangGraph que orquestra os agentes.
    
    Fluxo:
    1. Extrai mensagem e ID do usuário
    2. Mostra indicador "digitando..." no Telegram
    3. Executa workflow LangGraph (Partner → Finance/Setup → Output)
    4. Envia resposta formatada ao usuário
    
    Para debug:
    - Erros são logados no console
    - Mensagem genérica é enviada ao usuário em caso de erro
    - Use logs dos agentes para rastrear o fluxo
    
    Args:
        update: Objeto Update do Telegram com informações da mensagem
        context: Contexto do bot (não usado aqui, mas necessário pela API)
    """
    # Extrai informações da mensagem
    user_message = update.message.text
    user_id = str(update.effective_user.id)  # ID único do usuário no Telegram

    # Mostra indicador "digitando..." no Telegram enquanto processa
    await update.message.reply_chat_action("typing")
    
    try:
        # Executa workflow LangGraph de forma assíncrona
        # O workflow é síncrono, então usamos run_in_executor para não bloquear
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,  # Usa executor padrão
            partial(run_workflow, user_id, user_message)  # Função a executar
        )
        
        # Extrai resposta do resultado do workflow
        # O workflow retorna um dict com "response" contendo a mensagem final
        bot_response = result.get("response", "Não consegui processar sua mensagem.")
        
        # Envia resposta formatada ao usuário
        # Tenta enviar com Markdown, mas se falhar, envia sem formatação
        try:
            await update.message.reply_text(
                bot_response,
                parse_mode="Markdown"
            )
        except Exception as parse_error:
            # Se houver erro de parsing Markdown, tenta limpar e enviar novamente
            print(f"⚠️  Erro ao parsear Markdown: {parse_error}")
            try:
                # Tenta enviar sem formatação Markdown
                safe_response = safe_markdown(bot_response)
                await update.message.reply_text(safe_response, parse_mode=None)
            except Exception as e2:
                # Se ainda falhar, envia texto completamente limpo
                print(f"⚠️  Erro ao enviar mensagem limpa: {e2}")
                clean_response = bot_response.replace("*", "").replace("_", "").replace("`", "").replace("[", "").replace("]", "")
                await update.message.reply_text(clean_response)
        
    except Exception as e:
        # Em caso de erro, loga no console e envia mensagem genérica ao usuário
        # IMPORTANTE: Não exponha detalhes do erro ao usuário por segurança
        print(f"❌ Erro ao processar workflow: {e}")
        import traceback
        traceback.print_exc()  # Para debug completo no console
        
        await update.message.reply_text(
            "Desculpe, estou com problemas técnicos agora. "
            "Tente novamente em alguns instantes!"
        )


def main():
    """
    Função principal que inicia o bot do Telegram.
    
    Esta função:
    1. Inicializa o banco de dados (cria tabelas se não existirem)
    2. Cria a aplicação do Telegram
    3. Registra handlers para comandos e mensagens
    4. Inicia o bot em modo polling (fica escutando mensagens)
    
    Para parar o bot: Pressione Ctrl+C no terminal
    
    Handlers registrados:
    - /start → função start() (mensagem de boas-vindas)
    - Qualquer mensagem de texto → função handle_message() (processa via workflow)
    """
    print("🤖 Iniciando bot do Telegram...")

    # Inicializa banco de dados SQLite
    # Cria todas as tabelas necessárias se não existirem
    # IMPORTANTE: Sempre execute isso antes de iniciar o bot
    init_database()
    
    # Cria aplicação do Telegram usando o token
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Registra handlers (funções que respondem a eventos)
    # CommandHandler: responde a comandos como /start
    application.add_handler(CommandHandler("start", start))
    
    # MessageHandler: responde a mensagens de texto (exceto comandos)
    # filters.TEXT = apenas mensagens de texto
    # ~filters.COMMAND = exclui comandos (já tratados acima)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Inicia o bot em modo polling
    # Polling = fica fazendo requisições periódicas ao Telegram para buscar novas mensagens
    # allowed_updates=Update.ALL_TYPES = recebe todos os tipos de atualizações
    print("✅ Bot rodando! Pressione Ctrl+C para parar.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

