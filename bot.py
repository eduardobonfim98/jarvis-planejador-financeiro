"""Bot do Telegram - Jarvis."""
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# Carrega variáveis de ambiente
load_dotenv()

# Tokens
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise ValueError("⚠️ TELEGRAM_BOT_TOKEN não encontrado! Crie um arquivo .env com seu token.")

# Cliente OpenAI (opcional - se não tiver API key, usa resposta simples)
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
    print("✅ OpenAI configurado - Bot usando inteligência artificial!")
else:
    client = None
    print("⚠️ OPENAI_API_KEY não encontrado - Bot usando respostas simples")


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
    user_id = update.effective_user.id
    
    # Mostra que está processando
    await update.message.reply_chat_action("typing")
    
    if client:
        # Usa OpenAI para gerar resposta inteligente
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Você é o Jarvis, um assistente financeiro pessoal amigável e útil. "
                                 "Você ajuda pessoas a controlar seus gastos através do WhatsApp/Telegram. "
                                 "Seja empático, direto e sempre ofereça ajuda prática."
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            bot_response = response.choices[0].message.content
            await update.message.reply_text(bot_response)
            
        except Exception as e:
            print(f"❌ Erro ao chamar OpenAI: {e}")
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

