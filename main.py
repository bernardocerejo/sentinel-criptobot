import os
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime

# Ativa logging para debug
logging.basicConfig(level=logging.INFO)

# Variáveis do bot (usa as tuas variáveis de ambiente no Render ou localmente)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Exemplo: @SentinelSignals ou ID de chat

# Função que envia o sinal (exemplo simples)
async def enviar_sinal(context: ContextTypes.DEFAULT_TYPE):
    texto = f"🚨 Sinal automático enviado!\n🕒 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    # Enviar no chat onde foi usado /start
    await context.bot.send_message(chat_id=context.job.chat_id, text=texto)

# Comando /start
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 SentinelCriptoBot está ativo e pronto!")

    # Agenda enviar_sinal para 5 segundos depois, no chat que chamou /start
    context.job_queue.run_once(enviar_sinal, when=5, chat_id=update.effective_chat.id)

# Função principal para iniciar o bot
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Adicionar o handler do comando /start
    app.add_handler(CommandHandler("start", start))

    # Iniciar o bot (polling)
    app.run_polling()

if __name__ == '__main__':
    main()
