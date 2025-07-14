import logging
import os
import asyncio
from telegram import Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

# 📊 Lógica de IA simples para validar setups
def avaliar_setup(setup):
    score = 0
    if setup['estrutura'] == 'quebra de estrutura': score += 1
    if setup['order_block']: score += 1
    if setup['fvg']: score += 1
    if setup['rsi'] < 30 or setup['rsi'] > 70: score += 1
    if setup['volume'] > setup['media_volume']: score += 1
    return score  # Máximo: 5

# 🔐 Variáveis de ambiente do Render
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Ex: @SentinelSignals

bot = Bot(token=BOT_TOKEN)
logging.basicConfig(level=logging.INFO)

# 📩 Função principal que envia sinal
async def enviar_sinal(context: ContextTypes.DEFAULT_TYPE):
    setup = {
        'estrutura': 'quebra de estrutura',
        'order_block': True,
        'fvg': True,
        'rsi': 25,
        'volume': 1500,
        'media_volume': 1000
    }

    score = avaliar_setup(setup)
    if score < 4:
        print("❌ Setup rejeitado. Score:", score)
        return

    ativo = 'BTCUSDT'
    tp1 = '68.200'
    tp2 = '69.000'
    sl = '66.400'
    entrada = '67.100'

    texto = f"""
🚨 <b>NOVO SINAL: {ativo}</b>
📥 Entrada: <b>{entrada}</b>
🟢 TP1: {tp1}
🟢 TP2: {tp2}
🔴 SL: {sl}

🧠 Score de Confluência: <b>{score}/5</b>
🕒 {datetime.now().strftime('%d/%m/%Y %H:%M')}
    """
    await context.bot.send_message(chat_id=CHANNEL_ID, text=texto, parse_mode='HTML')

    # 📈 Gráfico com marcações visuais
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [float(sl), float(entrada), float(tp1)], marker='o')
    ax.axhline(y=float(tp1), color='green', linestyle='--', label='TP1')
    ax.axhline(y=float(tp2), color='green', linestyle='--', label='TP2')
    ax.axhline(y=float(sl), color='red', linestyle='--', label='SL')
    plt.title(f"{ativo} Setup")
    plt.legend()
    plt.savefig("grafico.png")
    await context.bot.send_photo(chat_id=CHANNEL_ID, photo=open("grafico.png", "rb"))

# /start para ativar o bot
async def start(update, context):
    await update.message.reply_text("🤖 SentinelCriptoBot está ativo e pronto!")

# MAIN
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    # ⏱️ Enviar um sinal 5 segundos depois do arranque
    # app.job_queue.run_once(enviar_sinal, 5)
    
    app.run_polling()


if __name__ == '__main__':
    main()
