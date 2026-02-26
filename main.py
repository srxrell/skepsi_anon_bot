
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

SIGNATURE = "•★•@SKEPSIanon_bot #тейк•★•"

BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_ID = os.getenv('GROUP_ID')
ADMIN_ID = os.getenv('ADMIN_ID')
CHANNEL_ID = os.getenv('CHANNEL_ID')


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для анонимных признаний.nn"
        "Просто отправьте мне ваше сообщение, и оно будет опубликовано анонимно "
        "с добавлением •★•@SKEPSIanon_bot #тейк•★•"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 Как использовать бота:nn"
        "Пишете свое размышление или идею, анонимно или с указанием своего юзернейма"
        "Команды:n"
        "/start - Начать работу с ботомn"
        "/help - Показать справку"
    )


async def forward_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пересылает сообщение в канал с добавлением подписи"""
    try:
        message_text = update.message.text
        
        if not message_text:
            return
        
        full_message = f"{message_text}nn{SIGNATURE}"
        
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=full_message,
            parse_mode='HTML'
        )
        
        await update.message.reply_text(
            "Ваше признание опубликовано анонимно!"
        )
        
        logger.info(f"Сообщение отправлено в канал {CHANNEL_ID}")
        
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при отправке сообщения. Попробуйте позже."
        )


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message.chat.type in ['group', 'supergroup']:
            message_text = update.message.text
            
            if not message_text:
                return
            
            full_message = f"{message_text}nn{SIGNATURE}"
            
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=full_message,
                parse_mode='HTML'
            )
            
            logger.info(f"Сообщение из группы переслано в канал")
            
    except Exception as e:
        logger.error(f"Ошибка при обработке группового сообщения: {e}")


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        forward_to_channel
    ))
    
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUP,
        handle_group_message
    ))
    
    logger.info("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
