import os
import json
import asyncio
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, CallbackContext,
)

# Variáveis do ambiente
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

STATUS_FILE = "status_sinais.json"

# Inicia status
def init_status():
    if not os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "w") as f:
            json.dump({"green": 0, "red": 0}, f)

def ler_status():
    with open(STATUS_FILE, "r") as f:
        return json.load(f)

def salvar_status(data):
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f)

def atualizar_contagem(status):
    data = ler_status()
    if status == "green":
        data["green"] += 1
    elif status == "red":
        data["red"] += 1
    salvar_status(data)

def avaliar_setup(setup):
    score = 0
    if setup['estrutura'] == 'quebra de estrutura': score += 1
    if setup['order_block']: score += 1
    if setup['fvg']: score += 1
    if setup['rsi'] < 30 or setup['rsi'] > 70: score += 1
    if setup['volume'] > setup['media_volume']: score += 1
    return score

async def enviar_sinal(context: CallbackContext, setup=None):
    if setup is None:
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
        print(f"❌ Setup rejeitado. Score: {score}")
        atualizar_contagem("red")
        return

    ativo = 'BTCUSDT'
    entrada = 67100
    tp1 = 68200
    tp2 = 69000
    sl = 66400

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

    # Gráfico
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [sl, entrada, tp1], marker='o')
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

    atualizar_contagem("green")

# Comandos
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 SentinelCriptoBot está ativo e pronto!")

async def comando_sinal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1 or context.args[0].lower() not in ["green", "red"]:
        await update.message.reply_text("Usa: /sinal green ou /sinal red")
        return
    status = context.args[0].lower()
    atualizar_contagem(status)
    await update.message.reply_text(f"Sinal '{status}' registrado!")

# Resumo semanal
async def resumo_semanal(context: CallbackContext):
    data = ler_status()
    texto = f"""
📊 <b>Resumo Semanal</b>

✅ Green: {data['green']}
❌ Red: {data['red']}

📅 {datetime.now().strftime('%d/%m/%Y')}
"""
    await context.bot.send_message(chat_id=CHANNEL_ID, text=texto, parse_mode='HTML')
    salvar_status({"green": 0, "red": 0})

def agendar_resumo(application):
    application.job_queue.run_daily(
        resumo_semanal,
        time=datetime.strptime("22:00", "%H:%M").time(),
        days=(6,)
    )

# Main
async def main():
    init_status()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sinal", comando_sinal))

    agendar_resumo(app)

    # Sinal automático de teste após 10s
    async def sinal_de_teste():
        await asyncio.sleep(10)
        await enviar_sinal(CallbackContext.from_update(None, app))

    asyncio.create_task(sinal_de_teste())

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())
