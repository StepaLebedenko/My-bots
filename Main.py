import os
import random
import threading
from flask import Flask
import telebot
from google import genai
from google.genai import types

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

# 2. Вставь свои токены в кавычки ""
TELEGRAM_TOKEN = "8862473984:AAFrlUGDAjDn4wb_QDHV8_xI9MTqjCbHiNg" 
GEMINI_API_KEY = "AQ.Ab8RN6J72RMbTCr-XI3IXNYGjVTIsTeVCR5gYik1pQQSa8ctvA" 

bot = telebot.TeleBot(TELEGRAM_TOKEN)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

user_chats = {}

GREETINGS = [
    "Здравствуйте! Я ваш персональный ИИ-ассистент. Чем я могу вам помочь?",
    "Приветствую! Готов ответить на ваши вопросы и помочь с решением задач. Что вас интересует?",
    "Здравствуйте! На связи ваш интеллектуальный помощник. Задайте ваш вопрос.",
    "Приветствую! Я готов к работе. Напишите, какую задачу необходимо решить."
]

SYSTEM_INSTRUCTION = (
    "Ты — профессиональный, компетентный и вежливый ИИ-ассистент. "
    "Твоя задача — давать точные, структурированные, объективные и исчерпывающие ответы на русском языке. "
    "Отвечай строго по существу, без использования сленга, юмора, шуток и лишней эмоциональности. "
    "Для удобства чтения используй четкое форматирование: списки, выделения ключевых мыслей жирным шрифтом и абзацы."
)

def get_or_create_chat(user_id):
    if user_id not in user_chats:
        user_chats[user_id] = ai_client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.3,
            )
        )
    return user_chats[user_id]

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    if user_id in user_chats:
        del user_chats[user_id]
        
    get_or_create_chat(user_id)
    
    welcome_text = random.choice(GREETINGS)
    welcome_text += "\n\n💡 *Примечание:* Чтобы очистить историю текущего диалога и начать обсуждение заново, воспользуйтесь командой `/reset`."
    bot.send_message(user_id, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['reset'])
def reset_memory(message):
    user_id = message.chat.id
    if user_id in user_chats:
        del user_chats[user_id]
    get_or_create_chat(user_id)
    bot.reply_to(message, "🧹 *История диалога успешно очищена.* Теперь вы можете начать обсуждение с чистого листа.", parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    chat = get_or_create_chat(user_id)
    
    bot.send_chat_action(user_id, 'typing')

    try:
        response = chat.send_message(message.text)
        bot.send_message(user_id, response.text, parse_mode="Markdown")

    except Exception as e:
        error_msg = "⚠️ Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте повторить отправку или используйте команду `/reset`."
        bot.send_message(user_id, error_msg)

if __name__ == "__main__":
    bot.infinity_polling()
