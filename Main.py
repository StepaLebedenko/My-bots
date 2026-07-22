from groq import Groq
import telebot

# --- ТВОИ ТОКЕНЫ И КЛЮЧИ ---
TELEGRAM_TOKEN = "8862473984:AAFrlUGDAjDn4wb_QDHV8_xI9MTqjCbHiNg"
GROQ_API_KEY = "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"

# Инициализация
bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = Groq(api_key=GROQ_API_KEY)


# Команда /start
@bot.message_handler(commands=["start"])
def send_welcome(message):
  text = (
      "Здравствуйте, царь батюшка! 👑\n\n"
      "Я ваш личный помощник на базе ИИ. Напишите любой вопрос или задачу!"
  )
  bot.reply_to(message, text)


# Обработка сообщений через Groq
@bot.message_handler(func=lambda message: True)
def handle_ai_response(message):
  bot.send_chat_action(message.chat.id, "typing")

  try:
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты — верный личный помощник. Всегда обращайся к"
                    " пользователю «царь батюшка»."
                ),
            },
            {"role": "user", "content": message.text},
        ],
        temperature=0.7,
    )

    answer = completion.choices[0].message.content
    bot.reply_to(message, answer)

  except Exception as e:
    print(f"Ошибка: {e}")
    bot.reply_to(
        message,
        "Ох, царь батюшка, произошла кручина (ошибка при обращении к ИИ)!",
    )


# Запуск бота
print("Бот запущен на сервере...")
bot.infinity_polling()
