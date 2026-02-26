import json
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
        if not update.message or not update.message.text:
            return
        
        full_message = f"{update.message.text}\n\n{SIGNATURE}"
        
        # Отправка в канал
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=full_message,
            parse_mode='HTML'
        )
        await update.message.reply_text("✅ Опубликовано!")
        logger.info(f"Сообщение отправлено в канал {CHANNEL_ID}")
        
    except Exception as e:
        logger.error(f"Ошибка при пересылке: {e}")
        await update.message.reply_text("❌ Ошибка. Проверь, что бот — админ в канале.")

# --- ЛОГИКА ВЕБХУКА ---

# Создаем приложение заранее
application = Application.builder().token(BOT_TOKEN).build()

async def telegram_webhook(request):
    try:
        # Читаем тело запроса
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        
        # Превращаем JSON в объект Update
        update = Update.de_json(data, application.bot)
        
        # Обрабатываем обновление
        await application.process_update(update)
        
        return Response("OK", status_code=200)
    except Exception as e:
        logger.error(f"КРИТИЧЕСКАЯ ОШИБКА ВЕБХУКА: {e}", exc_info=True)
        # Возвращаем 200 даже при ошибке, чтобы Telegram не спамил повторами при баге в коде
        return Response("Error handled", status_code=200)

async def health_check(request):
    return Response("I am alive", status_code=200)

# Добавляем обработчики
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_to_channel))

# Настройка веб-сервера
starlette_app = Starlette(
    routes=[
        Route("/webhook", telegram_webhook, methods=["POST"]),
        Route("/", health_check, methods=["GET"]),
    ]
)

async def main():
    # Установка вебхука
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    await application.bot.set_webhook(url=webhook_url)
    logger.info(f"Вебхук установлен на: {webhook_url}")
    
    port = int(os.getenv("PORT", 8080))
    config = uvicorn.Config(starlette_app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    
    async with application:
        await application.start()
        await server.serve()
        await application.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
