import os
import random
import telebot
from groq import Groq

# 1. Токены и ключи
TELEGRAM_TOKEN = "8862473984:AAFrlUGDAjDn4wb_QDHV8_xI9MTqjCbHiNg" 
GROQ_API_KEY = "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"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)

# Хранилище истории диалогов для каждого пользователя
user_contexts = {}

# 2. Прикольные и рофляные приветствия
GREETINGS = [
    "О, кто это тут у нас? 👋 Чего надобно, челобитный? Задавай вопрос, пока я добрый!",
    "Салам алейкум / Шалом / Привет! 🤖 Мои кремниевые мозги готовы к твоим жизненным задачам. Включай фантазию!",
    "Йоу! На связи главный ИИ-сверхразум этого чата. 🚀 О чем потрещим?",
    "Ало-ало! Сервера работают, нейроны шевелятся. Выкладывай, с чем пришел!"
]

# 3. Системная инструкция для ИИ (Задаем настроение и юмор!)
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Ты — веселый, ироничный и остроумный ИИ-ассистент с отличным чувством юмора. "
        "Твоя задача — отвечать на любые вопросы пользователя максимально понятно и полезно, "
        "но делать это с легким приколом, подколами, шутками, рофлами и свежими мемами (где это уместно). "
        "Будь ровным пацаном/другом, подбадривай пользователя, используй современный сленг, "
        "эмодзи, жирный текст и форматирование. Но главное — сам ответ на вопрос всё равно должен быть правильным и точным!"
    )
}

# 4. Обработка команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    # Очищаем историю при старте
    user_contexts[user_id] = [SYSTEM_PROMPT]
    
    # Выбираем случайное шутливое приветствие
    welcome_text = random.choice(GREETINGS)
    welcome_text += "\n\n🧹 *Кстати:* Если я начну слишком сильно заигрываться и наглеть, введи `/reset` — и я забуду всё, о чем мы болтали!"
    
    bot.send_message(user_id, welcome_text, parse_mode="Markdown")

# 5. Обработка команды /reset (Сброс памяти бота)
@bot.message_handler(commands=['reset'])
def reset_memory(message):
    user_id = message.chat.id
    user_contexts[user_id] = [SYSTEM_PROMPT]
    bot.reply_to(message, "🧹 *Стираем память!* Всё, я забыл все твои секреты. Давай по новой, Миша, всё переделываем!", parse_mode="Markdown")

# 6. Обработка текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    
    if user_id not in user_contexts:
        user_contexts[user_id] = [SYSTEM_PROMPT]
    
    # Добавляем сообщение пользователя
    user_contexts[user_id].append({"role": "user", "content": message.text})
    
    # Ограничиваем историю последних сообщений
    if len(user_contexts[user_id]) > 11:
        user_contexts[user_id] = [SYSTEM_PROMPT] + user_contexts[user_id][-10:]

    # Статус "печатает..."
    bot.send_chat_action(user_id, 'typing')

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=user_contexts[user_id],
            temperature=0.85, # Чуть подняли температуру для большей креативности и юмора
            max_tokens=1024
        )
        
        bot_response = completion.choices[0].message.content
        user_contexts[user_id].append({"role": "assistant", "content": bot_response})
        
        bot.send_message(user_id, bot_response, parse_mode="Markdown")

    except Exception as e:
        error_msg = "⚠️ Ой, мои микросхемы перегрелись от такого вопроса! Попробуй еще раз или шлепни `/reset`."
        bot.send_message(user_id, error_msg)

# Запуск
if __name__ == "__main__":
    bot.infinity_polling()
