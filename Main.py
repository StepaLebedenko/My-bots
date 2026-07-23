
    
import asyncio
import logging
import os
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web
from groq import Groq  # Библиотека Groq

# --- НАСТРОЙКИ КЛЮЧЕЙ ---
BOT_TOKEN = "8862473984:AAFrlUGDAjDn4wb_QDHV8_xI9MTqjCbHiNg" 
GROQ_API_KEY = "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" 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN.strip())
dp = Dispatcher()

# Инициализация клиента Groq
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# --- ВЕБ-СЕРВЕР ДЛЯ РЕНДЕРА (WEB SERVICE) ---
async def handle_ping(request):
    return web.Response(text="Bot is live on Groq!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- ФУНКЦИЯ ЗАПРОСА К GROQ AI ---
def ask_groq(prompt: str) -> str:
    """Молниеносная генерация через Groq API"""
    if not groq_client:
        return None
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Флагманская быстрая модель Groq
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Ошибка Groq API: {e}")
        return None

# --- ХРАНИЛИЩЕ СОСТОЯНИЯ ВИКТОРИН ---
# {chat_id: {"question": str, "answer": str, "hint": str}}
active_quizzes = {}

# --- КОМАНДЫ ---

@dp.message(Command("start", "help"))
async def cmd_start(message: types.Message):
    await message.answer(
        "⚡ **Игровой Groq ИИ-Бот для Чата!**\n\n"
        "**Команды для игр:**\n"
        "• `/quiz` — начать викторину с бесконечными вопросами от Groq ИИ 🧠\n"
        "• `/skip` — пропустить текущий вопрос, если никто не знает ответ ⏭️\n"
        "• `/mine` — командное минное поле 💣",
        parse_mode="Markdown"
    )

# --- ИГРА 1: ВИКТОРИНА С ВОЗМОЖНОСТЬЮ ПРОПУСКА ---

@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    chat_id = message.chat.id
    if chat_id in active_quizzes:
        await message.reply(
            "⚠️ В чате уже идет викторина!\n"
            "Если не знаете ответ, нажмите кнопку **«Пропустить»** под вопросом или напишите `/skip`."
        )
        return

    wait_msg = await message.answer("⚡ *Groq ИИ генерирует уникальный вопрос...*", parse_mode="Markdown")

    prompt = (
        "Сгенерируй один интересный и понятный вопрос для викторины (темы: видеоигры, кино, IT, общеизвестные факты).\n"
        "Формат ответа СТРОГО 3 строчки без лишнего текста:\n"
        "Вопрос: <текст вопроса>\n"
        "Ответ: <одно слово-ответ на русском>\n"
        "Подсказка: <короткая подсказка из 3-5 слов>"
    )

    ai_response = ask_groq(prompt)

    if not ai_response or "Ответ:" not in ai_response:
        # Резервный вопрос, если API недоступно
        q_text, a_text, h_text = "В какой игре главный герой — Геральт из Ривии?", "ведьмак", "Игра от CD Projekt Red"
    else:
        try:
            lines = [line.strip() for line in ai_response.split("\n") if line.strip()]
            q_text = lines[0].replace("Вопрос:", "").strip()
            a_text = lines[1].replace("Ответ:", "").strip().lower().replace(".", "")
            h_text = lines[2].replace("Подсказка:", "").strip() if len(lines) > 2 else "Нет подсказки"
        except Exception:
            q_text, a_text, h_text = "Как называется популярная игра-песочница из кубов?", "майнкрафт", "Разработана Mojang"

    active_quizzes[chat_id] = {
        "question": q_text,
        "answer": a_text,
        "hint": h_text
    }

    # Кнопки подсказки и пропуска
    builder = InlineKeyboardBuilder()
    builder.button(text="💡 Подсказка", callback_data="quiz_hint")
    builder.button(text="⏭️ Пропустить", callback_data="quiz_skip")
    builder.adjust(2)

    await wait_msg.edit_text(
        f"⚡ **GROQ ИИ-ВИКТОРИНА!**\n\n"
        f"❓ **Вопрос:** {q_text}\n\n"
        f"👇 *Пишите ответ (одно слово) прямо в чат!*",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

# Обработка команды /skip
@dp.message(Command("skip"))
async def cmd_skip(message: types.Message):
    chat_id = message.chat.id
    if chat_id not in active_quizzes:
        await message.reply("Сейчас нет активной викторины. Запусти её командой `/quiz`!")
        return

    correct_answer = active_quizzes[chat_id]["answer"].upper()
    del active_quizzes[chat_id]

    await message.answer(
        f"⏭️ Вопрос пропущен!\n"
        f"💡 Правильный ответ был: **{correct_answer}**\n\n"
        f"Запусти новую викторину командой `/quiz`!",
        parse_mode="Markdown"
    )

# Обработка кнопок Подсказки и Пропуска
@dp.callback_query(F.data.in_({"quiz_hint", "quiz_skip"}))
async def handle_quiz_buttons(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    if chat_id not in active_quizzes:
        await callback.answer("Эта викторина уже завершена!", show_alert=True)
        return

    if callback.data == "quiz_hint":
        hint = active_quizzes[chat_id]["hint"]
        await callback.answer(f"💡 Подсказка: {hint}", show_alert=True)

    elif callback.data == "quiz_skip":
        correct_answer = active_quizzes[chat_id]["answer"].upper()
        del active_quizzes[chat_id]

        await callback.message.edit_text(
            f"⏭️ **Игрок [{callback.from_user.first_name}] пропустил вопрос.**\n\n"
            f"💡 Правильный ответ был: **{correct_answer}**\n\n"
            f"Напишите `/quiz`, чтобы сыграть снова!",
            parse_mode="Markdown"
        )

# Проверка ответов в чате
@dp.message(~F.text.startswith("/"))
async def check_answers(message: types.Message):
    chat_id = message.chat.id
    if chat_id not in active_quizzes:
        return

    user_text = message.text.strip().lower()
    correct_answer = active_quizzes[chat_id]["answer"]

    if user_text == correct_answer or (len(user_text) > 3 and user_text in correct_answer):
        del active_quizzes[chat_id]
        await message.reply(
            f"🎉 **ПРАВИЛЬНО!** [{message.from_user.first_name}](tg://user?id={message.from_user.id}) угадал слово **{correct_answer.upper()}**!",
            parse_mode="Markdown"
        )

# --- ИГРА 2: МИННОЕ ПОЛЕ ---
@dp.message(Command("mine"))
async def cmd_mine(message: types.Message):
    bomb_index = random.randint(0, 8)
    builder = InlineKeyboardBuilder()
    for i in range(9):
        builder.button(text="❓", callback_data=f"field_{i}_{bomb_index}")
    builder.adjust(3)

    await message.answer(
        "💣 **КОМАНДНЫЙ САПЁР!**\n\nНажимайте кнопки по очереди. Кто наступит на мину — подорвётся!",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data.startswith("field_"))
async def handle_minefield(callback: types.CallbackQuery):
    _, cell_idx_str, bomb_idx_str = callback.data.split("_")
    if int(cell_idx_str) == int(bomb_idx_str):
        await callback.answer("💥 БУУУМ!", show_alert=True)
        await callback.message.edit_text(f"💥 **ВЗРЫВ!** [{callback.from_user.first_name}] подорвал весь отряд!")
    else:
        await callback.answer("🪙 Безопасно!")
        reply_markup = callback.message.reply_markup
        for row in reply_markup.inline_keyboard:
            for btn in row:
                if btn.callback_data == callback.data:
                    btn.text = "🪙"
                    btn.callback_data = "disabled"
        await callback.message.edit_reply_markup(reply_markup=reply_markup)

# --- ЗАПУСК ---
async def main():
    await start_web_server()
    print("🚀 Игровой Groq-бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
 
