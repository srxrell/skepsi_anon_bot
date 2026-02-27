import json
import os
import logging
import asyncio
import uvicorn
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# В ЖОПУ ЛОГИРОВАНИЕ
#logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
#logger = logging.getLogger(__name__)

SIGNATURE = "•★•@SKEPSIanon_bot #тейк•★•"
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
ADMIN_FORUM_ID = os.getenv('ADMIN_FORUM_ID')
TOPIC_ID = os.getenv('TOPIC_ID')
RENDER_EXTERNAL_URL = os.getenv('RENDER_EXTERNAL_URL')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Вас приветствует официальный бот Skepsi Confession! Здесь с помощью него вы можете выложить свою исповедь в канал!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Чтобы опубликовать тейк, он должен соблюдать правила:\n\n1. Не должен содержать спам\n\n2.Не содержит оскорбления чей-то личности, расы, религии и прочее.\n\n3.Не содержит троллинг\n\n4.Сообщения не по теме канала также не будут рассматриваться!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Разрешить", callback_data="pub_yes"),
            InlineKeyboardButton("❌ Отклонить", callback_data="pub_no"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await context.bot.send_message(
            chat_id=ADMIN_FORUM_ID,
            message_thread_id=int(TOPIC_ID) if TOPIC_ID else None,
            text=f"**Опаньки, новый запрос:**\n\n{user_text}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        await update.message.reply_text("Ваш текст был отправлен модераторам. Пожалуйста подождите")
    except Exception as e:
        #logger.error(f"Ошибка при отправке админам: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    original_text = query.message.text.replace("Опаньки, новый запрос:", "").strip()

    if query.data == "pub_yes":
        try:
            full_message = f"{original_text}\n\n{SIGNATURE}"
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=full_message
            )
            await query.edit_message_text(text=f"✅ Опубликовано в канале!\n\n{original_text}")
        except Exception as e:
            await query.edit_message_text(text=f"❌ Ошибка публикации: {e}")
    
    elif query.data == "pub_no":
        await query.edit_message_text(text=f"🗑 Отклонено модератором.\n\n{original_text}")


application = Application.builder().token(BOT_TOKEN).build()

application.add_handler(CommandHandler("start", start_command))
application.add_handler(CallbackQueryHandler(button_callback))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

async def telegram_webhook(request):
    body = await request.body()
    data = json.loads(body.decode('utf-8'))
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return Response("OK", status_code=200)

starlette_app = Starlette(routes=[
    Route("/webhook", telegram_webhook, methods=["POST"]),
    Route("/", lambda r: Response("I am alive", status_code=200), methods=["GET"]),
])

async def main():
    await application.bot.set_webhook(url=f"{RENDER_EXTERNAL_URL}/webhook")
    port = int(os.getenv("PORT", 8080))
    config = uvicorn.Config(starlette_app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    async with application:
        await application.start()
        await server.serve()
        await application.stop()

if __name__ == "__main__":
    asyncio.run(main())
