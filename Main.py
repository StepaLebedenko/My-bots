import os
import threading
from flask import Flask
import telebot
from mistralai import Mistral

# 1. Заглушка веб-сервера для бесплатного тарифа Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

# 2. Вставь свои токены СТРОГО внутри кавычек ""
TELEGRAM_TOKEN = "8862473984:AAFrlUGDAjDn4wb_QDHV8_xI9MTqjCbHiNg"
MISTRAL_API_KEY = "jNEzWtPRWZZlnCvRFJRQX0stM9evK02S"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
ai_client = Mistral(api_key=MISTRAL_API_KEY)

user_histories = {}

SYSTEM_INSTRUCTION = {
    "role": "system",
    "content": (
        "Ты — высокоинтеллектуальный, грамотный и отзывчивый ИИ-ассистент. "
        "Давай исчерпывающие, умные и логичные ответы на русском языке. "
        "Используй абзацы и выделение ключевых мыслей жирным шрифтом."
    )
}

def get_user_history(user_id):
    if user_id not in user_histories:
        user_histories[user_id] = [SYSTEM_INSTRUCTION]
    return user_histories[user_id]

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_histories[user_id] = [SYSTEM_INSTRUCTION]
    
    welcome_text = (
        "👋 **Привет! Я твой умный ИИ-ассистент на базе Mistral AI.**\n\n"
        "Задавай любые вопросы, проси помочь с учебой, кодом или задачами!\n\n"
        "💡 *Сброс диалога:* команда `/reset`."
    )
    bot.send_message(user_id, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['reset'])
def reset_memory(message):
    user_id = message.chat.id
    user_histories[user_id] = [SYSTEM_INSTRUCTION]
    bot.reply_to(message, "🧹 *История диалога очищена!*", parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    history = get_user_history(user_id)
    
    history.append({"role": "user", "content": message.text})
    bot.send_chat_action(user_id, 'typing')

    try:
        # Запрос к умной бесплатной модели Mistral
        response = ai_client.chat.complete(
            model="mistral-small-latest",
            messages=history,
            temperature=0.7,
        )
        
        bot_reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": bot_reply})
        
        if len(history) > 16:
            user_histories[user_id] = [SYSTEM_INSTRUCTION] + history[-15:]

        bot.send_message(user_id, bot_reply, parse_mode="Markdown")

    except Exception as e:
        bot.send_message(user_id, f"⚠️ Ошибка: `{e}`", parse_mode="Markdown")

if __name__ == "__main__":
    bot.infinity_polling()
