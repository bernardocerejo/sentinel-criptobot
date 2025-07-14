import os
import json
import asyncio
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Variáveis do ambiente (definir no Render)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Pode ser "@seucanal" ou ID numérico

STATUS_FILE = "status_sinais.json"

# Inicia arquivo status se não existir
def init_status():
    if not os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "w") as f:
            json.dump({"green": 0, "red": 0}, f)

# Lê status atual
def ler_status():
    with open(STATUS_FILE, "r") as f:
        return json.load(f)

# Salva status atualizado
def salvar_status(data):
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f)

# Atualiza contagem green/red
def atualizar_contagem(status):
    data = ler_status()
    if status == "green":
        data["green"] += 1
    elif status == "red":
        data["red"] += 1
    salvar_status(data)

# Lógica simples para avaliar o setup e retornar score (exemplo)
def avaliar_setup(setup):
    score = 0
    if setup['estrutura'] == 'quebra de estrutura': score += 1
    if setup['order_block']: score += 1
    if setup['fvg']: score += 1
    if setup['rsi'] < 30 or setup['rsi'] > 70: score += 1
    if setup['volume'] > setup['media_volume']: score += 1
    return score  # Máximo 5

# Função que envia sinal (exemplo)
async def enviar_sinal(context: ContextTypes.DEFAULT_TYPE, setup=None):
    if setup is None:
        # Setup de exemplo
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
        atualizar_contagem("red")  # Sinal rejeitado = red (stop loss)
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

    # Enviar texto
    await context.bot.send_message(chat_id=CHANNEL_ID, text=texto, parse_mode='HTML')

    # Criar gráfico simples
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

    # Enviar gráfico
    with open("grafico.png", "rb") as photo:
        await context.bot.send_photo(chat_id=CHANNEL_ID, photo=photo)

    # Contagem: se score >=4, sinal considerado green (take profit esperado)
    atualizar_contagem("green")

# Comando /start
async def start(update, context):
    await update.message.reply_text("🤖 SentinelCriptoBot está ativo e pronto!")

# Comando /sinal para testar adicionar manualmente green/red
async def comando_sinal(update, context):
    if len(context.args) != 1 or context.args[0].lower() not in ["green", "red"]:
        await update.message.reply_text("Use: /sinal green ou /sinal red")
        return
    status = context.args[0].lower()
    atualizar_contagem(status)
    await update.message.reply_text(f"Sinal '{status}' registrado!")

# Enviar resumo semanal domingo às 22h
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

# Agendador que roda sempre e espera até domingo 22h para enviar resumo
async def agendador_resumo(app):
    while True:
        now = datetime.now()
        dias_ate_domingo = (6 - now.weekday()) % 7
        proximo_domingo_22h = (now + timedelta(days=dias_ate_domingo)).replace(hour=22, minute=0, second=0, microsecond=0)
        wait_segundos = (proximo_domingo_22h - now).total_seconds()
        if wait_segundos < 0:
            wait_segundos += 7*24*3600
        await asyncio.sleep(wait_segundos)
        await resumo_semanal(app.bot)

# Função principal
async def main():
    init_status()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sinal", comando_sinal))

    # Para testes: enviar um sinal automático 10s após iniciar
    async def sinal_automatico():
        await asyncio.sleep(10)
        await enviar_sinal(app)

    asyncio.create_task(sinal_automatico())
    asyncio.create_task(agendador_resumo(app))

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.get_event_loop().run_until_complete(main())
