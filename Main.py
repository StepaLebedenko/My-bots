import os
import asyncio
import urllib.parse
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_TOKEN = "8862473984:AAFrlUGDAjDn4wb_QDHV8_xI9MTqjCbHiNg" 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для генерации изображений.\n\n"
        "Отправь мне текстовое описание (лучше на английском), и я создам картинку!"
    )

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text.strip()
    if not prompt:
        return

    status_message = await update.message.reply_text("🎨 Генерирую изображение, подождите...")

    try:
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=flux&width=1024&height=1024&nologo=true"

        await update.message.reply_photo(
            photo=image_url,
            caption=f"✨ **Запрос:** {prompt}",
            parse_mode="Markdown"
        )
        await status_message.delete()

    except Exception as e:
        logging.error(f"Ошибка при генерации: {e}")
        await status_message.edit_text("❌ Произошла ошибка при создании изображения. Попробуйте ещё раз.")

async def main_async():
    if not TELEGRAM_TOKEN:
        raise ValueError("Переменная окружения TELEGRAM_TOKEN не задана!")

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))

    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        # Держим бота запущенным
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main_async())
