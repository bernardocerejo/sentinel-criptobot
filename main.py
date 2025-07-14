import os
import json
import asyncio
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Ex: "@seucanal"

STATUS_FILE = "status_sinais.json"

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
    return score  # Máximo 5

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 SentinelCriptoBot está ativo e pronto!")

async def comando_sinal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1 or context.args[0].lower() not in ["green", "red"]:
        await update.message.reply_text("Use: /sinal green ou /sinal red")
        return
    status = context.args[0].lower()
    atualizar_contagem(status)
    await update.message.reply_text(f"Sinal '{status}' registrado!")

async def resumo_semanal(context: ContextTypes.DEFAULT_TYPE):
    data = ler_status()
    texto = f"""
Resumo Semanal dos Sinais 📊

✅ Green (Take Profit): {data['green']}
❌ Red (Stop Loss): {data['red']}

Semana encerrada! Próxima começa já. 💪
"""
    await context.bot.send_message(chat_id=CHANNEL_ID, text=texto)
    salvar_status({"green": 0, "red": 0})

def agendar_resumo_diario(application: Application):
    application.job_queue.run_daily(
        resumo_semanal,
        time=datetime.strptime("22:00", "%H:%M").time(),
        days=(6,),  # Domingo
    )

async def main():
    init_status()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sinal", comando_sinal))

    agendar_resumo_diario(app)

    async def sinal_automatico(context):
        await enviar_sinal(context)

    app.job_queue.run_once(sinal_automatico, when=10)

    print("✅ Bot iniciado com sucesso.")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
