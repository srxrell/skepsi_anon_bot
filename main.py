import os
import logging
import asyncio
import uvicorn
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы из переменных окружения
SIGNATURE = "•★•@SKEPSIanon_bot #тейк•★•"
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
# URL твоего приложения на Render (например, https://my-bot.onrender.com)
RENDER_EXTERNAL_URL = os.getenv('RENDER_EXTERNAL_URL') 

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Приветствуем в Skepsi Confession\n\n"
        "Просто отправьте мне ваше сообщение, укажите анонимно оно или нет, и мы отправим его в канал"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 Как использовать бота:\n"
        "Пишете сообщение — я пересылаю его в канал анонимно.\n"
        "/start - Начать\n"
        "/help - Справка"
    )

async def forward_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.text:
            return
        
        full_message = f"{update.message.text}\n\n{SIGNATURE}"
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=full_message,
            parse_mode='HTML'
        )
        await update.message.reply_text("Ваше признание опубликовано анонимно!")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("❌ Ошибка при отправке.")

# --- ЛОГИКА ВЕБХУКА ---

async def telegram_webhook(request):
    """Обработка входящих обновлений от Telegram"""
    json_string = await request.body()
    update = Update.de_json(data=asyncio.loads(json_string), bot=application.bot)
    await application.process_update(update)
    return Response(status_code=200)

async def health_check(request):
    """Для проверки того, что сервис жив"""
    return Response("I am alive", status_code=200)

# Инициализация приложения Telegram
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_to_channel))

# Настройка веб-сервера Starlette
starlette_app = Starlette(
    routes=[
        Route("/webhook", telegram_webhook, methods=["POST"]),
        Route("/", health_check, methods=["GET"]),
    ]
)

async def main():
    # Установка вебхука в Telegram
    await application.bot.set_webhook(url=f"{RENDER_EXTERNAL_URL}/webhook")
    
    # Запуск сервера
    port = int(os.getenv("PORT", 8080))
    config = uvicorn.Config(starlette_app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    
    async with application:
        await application.start()
        await server.serve()
        await application.stop()

if __name__ == "__main__":
    asyncio.run(main())
