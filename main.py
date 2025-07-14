import logging
import os
import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from datetime import datetime
import matplotlib.pyplot as plt

# Configura logging
logging.basicConfig(level=logging.INFO)

# Variáveis de ambiente (definir no Render)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # ex: @SentinelSignals

bot = Bot(token=BOT_TOKEN)

# Avalia setup e retorna score 0-5
def avaliar_setup(setup):
    score = 0
    if setup['estrutura'] == 'quebra de estrutura': score += 1
    if setup['order_block']: score += 1
    if setup['fvg']: score += 1
    if setup['rsi'] < 30 or setup['rsi'] > 70: score += 1
    if setup['volume'] > setup['media_volume']: score += 1
    return score

async def enviar_sinal(context: ContextTypes.DEFAULT_TYPE, *,
                       ativo: str,
                       entrada: float,
                       tp1: float,
                       tp2: float,
                       sl: float,
                       prioridade: str,
                       tipo_trade: str,
                       setup: dict):
    
    score = avaliar_setup(setup)
    if score < 3:
        logging.info(f"Setup rejeitado (score {score}) para {ativo}")
        return
    
    # Mensagem formatada
    texto = f"""
🚨 <b>NOVO SINAL: {ativo}</b>
🔰 Prioridade: <b>{prioridade}</b>
⚡ Tipo de trade: <b>{tipo_trade}</b>
📥 Entrada: <b>{entrada:.2f}</b>
🟢 TP1: {tp1:.2f}
🟢 TP2: {tp2:.2f}
🔴 SL: {sl:.2f}

🧠 Score de Confluência: <b>{score}/5</b>
🕒 {datetime.now().strftime('%d/%m/%Y %H:%M')}
    """

    # Botões para possível ação (exemplo: fechar posição, etc)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Fechar Posição", callback_data=f"fechar_{ativo}")],
    ])

    await context.bot.send_message(chat_id=CHANNEL_ID, text=texto, parse_mode='HTML', reply_markup=keyboard)

    # Criar gráfico simples
    fig, ax = plt.subplots(figsize=(6,4))
    ax.plot([1, 2, 3, 4], [sl, entrada, tp1, tp2], marker='o')
    ax.axhline(y=tp1, color='green', linestyle='--', label='TP1')
    ax.axhline(y=tp2, color='green', linestyle='--', label='TP2')
    ax.axhline(y=sl, color='red', linestyle='--', label='SL')
    plt.title(f"{ativo} Setup")
    plt.legend()
    plt.tight_layout()
    plt.savefig("grafico.png")
    plt.close(fig)

    with open("grafico.png", "rb") as photo:
        await context.bot.send_photo(chat_id=CHANNEL_ID, photo=photo)


# /start handler
async def start(update, context):
    await update.message.reply_text("🤖 SentinelCriptoBot está ativo e pronto!")

# Função para exemplo enviar sinal no arranque
async def start_jobs(app):
    await asyncio.sleep(5)

    setup_exemplo = {
        'estrutura': 'quebra de estrutura',
        'order_block': True,
        'fvg': True,
        'rsi': 25,
        'volume': 1500,
        'media_volume': 1000
    }

    await enviar_sinal(
        context=app,
        ativo='BTCUSDT',
        entrada=67100,
        tp1=68200,
        tp2=69000,
        sl=66400,
        prioridade='Alta',
        tipo_trade='Swing',
        setup=setup_exemplo
    )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    # Inicia tarefa que envia sinal de exemplo após 5s
    asyncio.create_task(start_jobs(app))

    app.run_polling()

if __name__ == '__main__':
    main()
