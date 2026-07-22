import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Конфигурация ключей
TELEGRAM_BOT_TOKEN = "8862473984:AAFrlUGDAjDn4wb_QDHV8_xI9MTqjCbHiNg"
DEEPSEEK_API_KEY = "sk-963bbd220c9a44d69d735664e490934b"

# Инициализация клиентов
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# DeepSeek использует клиент OpenAI, но с указанием своего base_url
client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# Обработчик команды /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("Привет! Напиши мне любой вопрос, и я отвечу с помощью DeepSeek.")

# Обработчик всех текстовых сообщений
@dp.message()
async def handle_message(message: types.Message):
    # Отправляем плашку "печатает...", чтобы пользователь видел активность
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        # Запрос к API DeepSeek
        response = await client.chat.completions.create(
            model="deepseek-chat",  # Для логических задач можно использовать "deepseek-reasoner"
            messages=[
                {"role": "system", "content": "Ты полезный и вежливый ассистент."},
                {"role": "user", "content": message.text}
            ],
            stream=False
        )

        # Получаем ответ и отправляем пользователю
        answer = response.choices[0].message.content
        await message.answer(answer)

    except Exception as e:
        logging.error(f"Ошибка при запросе к DeepSeek: {e}")
        await message.answer("Произошла ошибка при обработке запроса. Попробуйте позже.")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
