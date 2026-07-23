import asyncio
import logging
import os
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from groq import Groq

# --- НАСТРОЙКИ КЛЮЧЕЙ ---
BOT_TOKEN = "8862473984:AAFrlUGDAjDn4wb_QDHV8_xI9MTqjCbHiNg" 
GROQ_API_KEY = "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" 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN.strip())
dp = Dispatcher()

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# --- ФУНКЦИЯ ЗАПРОСА К GROQ AI ---
def ask_groq(prompt: str) -> str:
    if not groq_client:
        return None
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=400,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Ошибка Groq API: {e}")
        return None

# --- ХРАНИЛИЩА СОСТОЯНИЙ ИГР ---
active_quizzes = {}   
active_riddles = {}   
active_mafia = {}     

# --- КОМАНДЫ ---

@dp.message(Command("start", "help"))
async def cmd_start(message: types.Message):
    await message.answer(
        "⚡ **Игровой Groq ИИ-Бот для Чата!**\n\n"
        "🎮 **Коллективные игры:**\n"
        "• `/quiz` — ИИ-викторина 🧠\n"
        "• `/riddle` — Загадки ИИ 🕵️‍♂️\n"
        "• `/skip` — Пропустить вопрос ⏭️\n"
        "• `/mafia` — Быстрая мафия 🕵️‍♀️\n"
        "• `/roast` (ответом) — ИИ-прожарка 🔥\n"
        "• `/mine` — Сапёр 💣",
        parse_mode="Markdown"
    )

@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    chat_id = message.chat.id
    if chat_id in active_quizzes or chat_id in active_riddles:
        await message.reply("⚠️ Игра уже идет! Завершите ее или напишите `/skip`.")
        return

    wait_msg = await message.answer("⚡ *Groq ИИ генерирует вопрос...*", parse_mode="Markdown")
    prompt = (
        "Сгенерируй один интересный вопрос для викторины.\n"
        "Формат ответа СТРОГО 3 строчки:\n"
        "Вопрос: <текст>\n"
        "Ответ: <одно слово>\n"
        "Подсказка: <короткая подсказка>"
    )
    ai_response = ask_groq(prompt)

    if not ai_response or "Ответ:" not in ai_response:
        q_text, a_text, h_text = "В какой игре главный герой — Геральт?", "ведьмак", "От CD Projekt Red"
    else:
        try:
            lines = [line.strip() for line in ai_response.split("\n") if line.strip()]
            q_text = lines[0].replace("Вопрос:", "").strip()
            a_text = lines[1].replace("Ответ:", "").strip().lower().replace(".", "")
            h_text = lines[2].replace("Подсказка:", "").strip() if len(lines) > 2 else "Нет подсказки"
        except Exception:
            q_text, a_text, h_text = "Песочница из кубов?", "майнкрафт", "Разработана Mojang"

    active_quizzes[chat_id] = {"question": q_text, "answer": a_text, "hint": h_text}

    builder = InlineKeyboardBuilder()
    builder.button(text="💡 Подсказка", callback_data="quiz_hint")
    builder.button(text="⏭️ Пропустить", callback_data="quiz_skip")
    builder.adjust(2)

    await wait_msg.edit_text(
        f"⚡ **ИИ-ВИКТОРИНА!**\n\n❓ **Вопрос:** {q_text}\n\n👇 *Пишите ответ в чат!*",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.message(Command("riddle"))
async def cmd_riddle(message: types.Message):
    chat_id = message.chat.id
    if chat_id in active_quizzes or chat_id in active_riddles:
        await message.reply("⚠️ Игра уже идет! Напишите `/skip` для пропуска.")
        return

    wait_msg = await message.answer("🕵️‍♂️ *Groq ИИ загадывает предмет...*", parse_mode="Markdown")
    prompt = (
        "Загадай популярный предмет или персонажа из игр/кино.\n"
        "Формат СТРОГО 2 строчки:\n"
        "Загадка: <3 улики через точку с запятой>\n"
        "Ответ: <одно слово>"
    )
    ai_response = ask_groq(prompt)

    if not ai_response or "Ответ:" not in ai_response:
        r_text, a_text = "Зеленый; Из блоков; Взрывается", "крипер"
    else:
        try:
            lines = [line.strip() for line in ai_response.split("\n") if line.strip()]
            r_text = lines[0].replace("Загадка:", "").strip()
            a_text = lines[1].replace("Ответ:", "").strip().lower().replace(".", "")
        except Exception:
            r_text, a_text = "Красная кепка; Собирает монеты; Спасает принцессу", "марио"

    active_riddles[chat_id] = {"answer": a_text}

    builder = InlineKeyboardBuilder()
    builder.button(text="⏭️ Пропустить", callback_data="riddle_skip")

    await wait_msg.edit_text(
        f"🕵️‍♂️ **ИИ-ЗАГАДКА!**\n\n📜 **Улики:** {r_text}\n\n👇 *Отгадывайте в чате!*",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.message(Command("skip"))
async def cmd_skip(message: types.Message):
    chat_id = message.chat.id
    if chat_id in active_quizzes:
        ans = active_quizzes[chat_id]["answer"].upper()
        del active_quizzes[chat_id]
        await message.answer(f"⏭️ Пропущено! Ответ: **{ans}**", parse_mode="Markdown")
    elif chat_id in active_riddles:
        ans = active_riddles[chat_id]["answer"].upper()
        del active_riddles[chat_id]
        await message.answer(f"⏭️ Пропущено! Ответ: **{ans}**", parse_mode="Markdown")
    else:
        await message.answer("Сейчас нет активной игры.")

@dp.callback_query(F.data.in_({"quiz_hint", "quiz_skip", "riddle_skip"}))
async def handle_game_buttons(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    if callback.data == "quiz_hint" and chat_id in active_quizzes:
        await callback.answer(f"💡 Подсказка: {active_quizzes[chat_id]['hint']}", show_alert=True)
    elif callback.data == "quiz_skip" and chat_id in active_quizzes:
        ans = active_quizzes[chat_id]["answer"].upper()
        del active_quizzes[chat_id]
        await callback.message.edit_text(f"⏭️ Вопрос пропущен. Ответ был: **{ans}**", parse_mode="Markdown")
    elif callback.data == "riddle_skip" and chat_id in active_riddles:
        ans = active_riddles[chat_id]["answer"].upper()
        del active_riddles[chat_id]
        await callback.message.edit_text(f"⏭️ Загадка пропущена. Ответ был: **{ans}**", parse_mode="Markdown")

@dp.message(~F.text.startswith("/"))
async def check_chat_answers(message: types.Message):
    chat_id = message.chat.id
    text = message.text.strip().lower()

    if chat_id in active_quizzes:
        ans = active_quizzes[chat_id]["answer"]
        if text == ans or (len(text) > 3 and text in ans):
            del active_quizzes[chat_id]
            await message.reply(f"🎉 **ВЕРНО!** [{message.from_user.first_name}](tg://user?id={message.from_user.id}) угадал: **{ans.upper()}**!", parse_mode="Markdown")

    elif chat_id in active_riddles:
        ans = active_riddles[chat_id]["answer"]
        if text == ans or (len(text) > 3 and text in ans):
            del active_riddles[chat_id]
            await message.reply(f"🎉 **ОТГАДАНО!** [{message.from_user.first_name}](tg://user?id={message.from_user.id}) разгадал: **{ans.upper()}**!", parse_mode="Markdown")

@dp.message(Command("roast"))
async def cmd_roast(message: types.Message):
    if not message.reply_to_message or message.reply_to_message.from_user.is_bot:
        await message.reply("⚠️ Ответь этой командой на сообщение друга!")
        return

    target_name = message.reply_to_message.from_user.first_name
    prompt = f"Напиши один смешной и дружеский подкол для человека по имени {target_name}. Максимум 2 предложения."
    
    wait_msg = await message.answer("🔥 *Придумываю подкол...*", parse_mode="Markdown")
    roast_text = ask_groq(prompt) or f"{target_name} сегодня экономит энергию!"
    await wait_msg.edit_text(f"🔥 **ПРОЖАРКА ДЛЯ [{target_name}]:**\n\n_{roast_text}_", parse_mode="Markdown")

@dp.message(Command("mafia"))
async def cmd_mafia(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🕵️‍♂️ Присоединиться (0/3)", callback_data="mafia_join")
    await message.answer("🕵️‍♀️ **МАФИЯ (3 игрока)**\nНажмите кнопку ниже!", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "mafia_join")
async def handle_mafia_join(callback: types.CallbackQuery):
    msg_id = callback.message.message_id
    user = callback.from_user
    if msg_id not in active_mafia:
        active_mafia[msg_id] = {"players": {}}

    players = active_mafia[msg_id]["players"]
    if user.id in players:
        await callback.answer("Ты уже в игре!", show_alert=True)
        return

    players[user.id] = user.first_name
    await callback.answer("Ты в игре!")

    if len(players) < 3:
        builder = InlineKeyboardBuilder()
        builder.button(text=f"🕵️‍♂️ Присоединиться ({len(players)}/3)", callback_data="mafia_join")
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    else:
        p_ids = list(players.keys())
        random.shuffle(p_ids)
        roles = {p_ids[0]: "🔪 Мафия", p_ids[1]: "🔍 Детектив", p_ids[2]: "👑 Мэр"}

        for p_id, role in roles.items():
            try:
                await bot.send_message(p_id, f"🤫 Твоя роль: **{role}**", parse_mode="Markdown")
            except Exception:
                pass

        await callback.message.edit_text(
            f"🕵️‍♀️ **МАФИЯ НАЧАЛАСЬ!**\nИгроки: {players[p_ids[0]]}, {players[p_ids[1]]}, {players[p_ids[2]]}\n"
            f"🔪 **Мафия** среди вас! Обсудите и вычислите её!",
            parse_mode="Markdown"
        )
        del active_mafia[msg_id]

@dp.message(Command("mine"))
async def cmd_mine(message: types.Message):
    bomb_index = random.randint(0, 8)
    builder = InlineKeyboardBuilder()
    for i in range(9):
        builder.button(text="❓", callback_data=f"field_{i}_{bomb_index}")
    builder.adjust(3)
    await message.answer("💣 **САПЁР!** Кто наступит на мину — подорвётся!", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("field_"))
async def handle_minefield(callback: types.CallbackQuery):
    _, cell_idx_str, bomb_idx_str = callback.data.split("_")
    if int(cell_idx_str) == int(bomb_idx_str):
        await callback.answer("💥 БУУУМ!", show_alert=True)
        await callback.message.edit_text(f"💥 **ВЗРЫВ!** [{callback.from_user.first_name}] подорвался!")
    else:
        await callback.answer("🪙 Безопасно!")
        reply_markup = callback.message.reply_markup
        for row in reply_markup.inline_keyboard:
            for btn in row:
                if btn.callback_data == callback.data:
                    btn.text = "🪙"
                    btn.callback_data = "disabled"
        await callback.message.edit_reply_markup(reply_markup=reply_markup)

# --- ЗАПУСК ПОЛЛИНГА ---
async def main():
    print("🚀 Игровой бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
