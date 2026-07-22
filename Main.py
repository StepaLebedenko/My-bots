import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiohttp import web
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

TELEGRAM_BOT_TOKEN = "8862473984:AAFrlUGDAjDn4wb_QDHV8_xI9MTqjCbHiNg" 
OPENROUTER_API_KEY = "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" 
MODEL_NAME = "deepseek/deepseek-r1:free"

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
ai_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY
)

user_history = {}


# --- ФЕЙКОВЫЙ ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def handle_healthcheck(request):
    return web.Response(text="Bot is running!")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_healthcheck)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render передает номер порта в переменную PORT
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


# --------------------------------------


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer("Привет! Я бот на базе OpenRouter.")


@dp.message()
async def chat_handler(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_history:
        user_history[user_id] = []

    user_history[user_id].append({"role": "user", "content": message.text})
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        response = await ai_client.chat.completions.create(
            model=MODEL_NAME, messages=user_history[user_id]
        )
        bot_response = response.choices[0].message.content
        user_history[user_id].append(
            {"role": "assistant", "content": bot_response}
        )
        await message.answer(bot_response)
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


async def main():
    # Запускаем и веб-сервер для Render, и сам поллинг бота
    await start_web_server()
    print("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
