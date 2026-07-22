import os
import random
import threading
from flask import Flask
import telebot
from openai import OpenAI

# 1. Заглушка веб-сервера для бесплатного Web Service на Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Запускаем веб-сервер в отдельном потоке
threading.Thread(target=run_flask, daemon=True).start()

# 2. Вставь свои токены СТРОГО внутри кавычек ""
TELEGRAM_TOKEN = "8862473984:AAFrlUGDAjDn4wb_QDHV8_xI9MTqjCbHiNg"
DEEPSEEK_API_KEY = "sk-963bbd220c9a44d69d735664e490934b"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Клиент DeepSeek
ai_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# Хранилище истории диалогов для каждого пользователя
user_histories = {}

# Приветственные сообщения
GREETINGS = [
    "Здравствуйте! Я ваш персональный ИИ-ассистент на базе DeepSeek. Чем могу помочь?",
    "Приветствую! Готов ответить на ваши вопросы и помочь с решением задач.",
    "Здравствуйте! На связи ваш умный помощник. Задавайте любой вопрос!",
    "Приветствую! Я готов к работе. Напишите, какую задачу нужно решить."
]

# Системная инструкция
SYSTEM_INSTRUCTION = {
    "role": "system",
    "content": (
        "Ты — профессиональный, компетентный и умный ИИ-ассистент. "
        "Твоя задача — давать точные, структурированные, логичные и исчерпывающие ответы на русском языке. "
        "Используй четкое форматирование: списки, абзацы и выделение ключевых мыслей жирным шрифтом."
    )
}

def get_user_history(user_id):
    """Возвращает или создает историю сообщений пользователя"""
    if user_id not in user_histories:
        user_histories[user_id] = [SYSTEM_INSTRUCTION]
    return user_histories[user_id]

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_histories[user_id] = [SYSTEM_INSTRUCTION]
    
    welcome_text = random.choice(GREETINGS)
    welcome_text += "\n\n💡 *Примечание:* Чтобы сбросить контекст и начать диалог заново, используйте команду `/reset`."
    bot.send_message(user_id, welcome_text, parse_mode="Markdown")

# Команда /reset (очистка памяти)
@bot.message_handler(commands=['reset'])
def reset_memory(message):
    user_id = message.chat.id
    user_histories[user_id] = [SYSTEM_INSTRUCTION]
    bot.reply_to(message, "🧹 *История диалога очищена.* Можем начать с чистого листа!", parse_mode="Markdown")

# Обработка текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    history = get_user_history(user_id)
    
    # Добавляем сообщение пользователя в историю
    history.append({"role": "user", "content": message.text})
    
    bot.send_chat_action(user_id, 'typing')

    try:
        # Запрос к нейросети DeepSeek
        response = ai_client.chat.completions.create(
            model="deepseek-chat", # Флагманская модель DeepSeek-V3
            messages=history,
            temperature=0.7,
            stream=False
        )
        
        bot_reply = response.choices[0].message.content
        
        # Сохраняем ответ бота в историю для контекста
        history.append({"role": "assistant", "content": bot_reply})
        
        # Ограничиваем историю (последние 20 сообщений), чтобы не переполнять память
        if len(history) > 21:
            user_histories[user_id] = [SYSTEM_INSTRUCTION] + history[-20:]

        bot.send_message(user_id, bot_reply, parse_mode="Markdown")

    except Exception as e:
        error_msg = "⚠️ Произошла ошибка при обращении к DeepSeek. Попробуйте еще раз или введите `/reset`."
        bot.send_message(user_id, error_msg)

if __name__ == "__main__":
    bot.infinity_polling()
