import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# 1. Вставь свои токены
TELEGRAM_BOT_TOKEN = "8862473984:AAFrlUGDAjDn4wb_QDHV8_xI9MTqjCbHiNg" 
OPENROUTER_API_KEY = "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"

# Выбери бесплатную модель
MODEL_NAME = "deepseek/deepseek-r1:free"

# 2. Инициализация бота и клиента OpenAI (настроенного под OpenRouter)
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

ai_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Хранилище истории сообщений для каждого пользователя
# Формат: {user_id: [{"role": "user/assistant", "content": "..."}]}
user_history = {}


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    # Очищаем историю при старте
    user_history[user_id] = [
        {
            "role": "system",
            "content": "Ты дружелюбный и умный AI-помощник в Telegram. Отвечай понятно и четко.",
        }
    ]
    await message.answer(
        "Привет! Я бот на базе нейросети через OpenRouter. Задавай любой вопрос!"
    )


@dp.message()
async def chat_handler(message: types.Message):
    user_id = message.from_user.id

    # Если пользователь пишет впервые без /start, инициализируем историю
    if user_id not in user_history:
        user_history[user_id] = [
            {
                "role": "system",
                "content": "Ты дружелюбный и умный AI-помощник в Telegram.",
            }
        ]

    # Добавляем сообщение пользователя в историю
    user_history[user_id].append({"role": "user", "content": message.text})

    # Ограничиваем историю (например, последние 10 сообщений), чтобы не переполнять контекст
    if len(user_history[user_id]) > 11:
        user_history[user_id] = [user_history[user_id][0]] + user_history[
            user_id
        ][-10:]

    # Отправляем плашку "печатает..."
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        # Делаем запрос к OpenRouter
        response = await ai_client.chat.completions.create(
            model=MODEL_NAME, messages=user_history[user_id]
        )

        bot_response = response.choices[0].message.content

        # Сохраняем ответ нейросети в историю
        user_history[user_id].append(
            {"role": "assistant", "content": bot_response}
        )

        # Отправляем ответ пользователю (с поддержкой Markdown)
        await message.answer(bot_response, parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"Произошла ошибка при обращении к нейросети: {e}")


async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
