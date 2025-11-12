"""Bot do Telegram - Jarvis."""
import asyncio
import os
from functools import partial

import google.generativeai as genai
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from database import init_database, save_message

# Carrega variáveis de ambiente
load_dotenv()

# Tokens
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

if not BOT_TOKEN:
    raise ValueError("⚠️ TELEGRAM_BOT_TOKEN não encontrado! Crie um arquivo .env com seu token.")

# Cliente Gemini (opcional - se não tiver API key, usa resposta simples)
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        print(f"✅ Gemini configurado ({GEMINI_MODEL_NAME}) - Bot usando inteligência artificial!")
    except Exception as exc:
        gemini_model = None
        print(f"❌ Erro ao configurar Gemini: {exc}")
else:
    gemini_model = None
    print("⚠️ GEMINI_API_KEY não encontrado - Bot usando respostas simples")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde ao comando /start."""
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
    """Processa mensagens com inteligência artificial."""
    user_message = update.message.text
    user_id = str(update.effective_user.id)

    # Registra interação básica no banco
    try:
        save_message(user_id, user_message)
    except Exception as db_error:
        print(f"⚠️ Não foi possível salvar a mensagem no banco: {db_error}")

    # Mostra que está processando
    await update.message.reply_chat_action("typing")
    
    if gemini_model:
        # Usa Gemini para gerar resposta inteligente
        try:
            prompt = (
                "Você é o Jarvis, um assistente financeiro pessoal amigável e útil. "
                "Ajude o usuário a controlar gastos, responder perguntas de finanças pessoais e "
                "oferecer apoio prático. Seja empático, direto e objetivo nas orientações.\n\n"
                f"Mensagem do usuário: {user_message}"
            )

            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                partial(gemini_model.generate_content, prompt)
            )

            bot_response = (getattr(response, "text", "") or "").strip()
            if not bot_response:
                bot_response = (
                    "Não consegui gerar uma resposta agora. "
                    "Pode repetir a pergunta?"
                )

            await update.message.reply_text(bot_response)

        except Exception as e:
            print(f"❌ Erro ao chamar Gemini: {e}")
            await update.message.reply_text(
                "Desculpe, estou com problemas técnicos agora. "
                "Tente novamente em alguns instantes!"
            )
    else:
        # Fallback: resposta simples sem API
        await update.message.reply_text("Tchau!")


def main():
    """Inicia o bot."""
    print("🤖 Iniciando bot do Telegram...")

    # Garante que o banco está pronto
    init_database()
    
    # Cria a aplicação
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Adiciona handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Inicia o bot
    print("✅ Bot rodando! Pressione Ctrl+C para parar.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

