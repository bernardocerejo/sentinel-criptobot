import os
import json
import asyncio
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Bot, Update 

# Variáveis do ambiente (definir no Render)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Pode ser "@seucanal" ou ID numérico

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
    return score

async def enviar_sinal(bot, setup=None):
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
    await bot.send_message(chat_id=CHANNEL_ID, text=texto, parse_mode='HTML')

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
        await bot.send_photo(chat_id=CHANNEL_ID, photo=photo)

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

async def resumo_semanal(bot):
    data = ler_status()
    texto = f"""
Resumo Semanal dos Sinais 📊

✅ Green (Take Profit): {data['green']}
❌ Red (Stop Loss): {data['red']}

Semana encerrada! Próxima começa já. 💪
"""
    await bot.send_message(chat_id=CHANNEL_ID, text=texto)
    salvar_status({"green": 0, "red": 0})

async def agendador_resumo(bot):
    while True:
        now = datetime.now()
        dias_ate_domingo = (6 - now.weekday()) % 7
        proximo_domingo_22h = (now + timedelta(days=dias_ate_domingo)).replace(hour=22, minute=0, second=0, microsecond=0)
        wait_segundos = (proximo_domingo_22h - now).total_seconds()
        if wait_segundos < 0:
            wait_segundos += 7*24*3600
        await asyncio.sleep(wait_segundos)
        await resumo_semanal(bot)

async def sinal_automatico(bot):
    await asyncio.sleep(10)
    await enviar_sinal(bot)

async def main():
    init_status()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sinal", comando_sinal))

    bot = Bot(BOT_TOKEN)

    asyncio.create_task(sinal_automatico(bot))
    asyncio.create_task(agendador_resumo(bot))

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
