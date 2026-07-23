import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = "8862473984:AAFrlUGDAjDn4wb_QDHV8_xI9MTqjCbHiNg "  # Вставь токен от BotFather

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ХРАНИЛИЩА СОСТОЯНИЙ ИГР ---
# 1. Активные вопросы викторины {chat_id: "ответ"}
active_quizzes = {}

# 2. Игры Камень-Ножницы-Бумага {msg_id: {"p1": id, "p2": id, "p1_move": str, "p2_move": str, "p1_name": str, "p2_name": str}}
rps_games = {}

# 3. База вопросов для викторины
QUIZ_QUESTIONS = [
    {"q": "В какой игре главный герой — Геральт из Ривии?", "a": ["ведьмак", "thewitcher", "witcher"]},
    {"q": "Какая компания создала консоль PlayStation?", "a": ["sony", "сони"]},
    {"q": "Как называется популярный песочный мир из кубов?", "a": ["minecraft", "майнкрафт"]},
    {"q": "В каком году вышла игра GTA V?", "a": ["2013"]},
    {"q": "Как зовут водопроводчика в красной кепке из игр Nintendo?", "a": ["марио", "mario"]},
]


# --- ИГРА 1: ВИКТОРИНА ДЛЯ ВСЕГО ЧАТА ---

@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    chat_id = message.chat.id
    if chat_id in active_quizzes:
        await message.reply("⚠️ В чате уже идет викторина! Ответьте на текущий вопрос.")
        return

    item = random.choice(QUIZ_QUESTIONS)
    active_quizzes[chat_id] = item["a"]

    await message.answer(
        f"🧠 **ВИКТОРИНА ДЛЯ ВСЕХ!**\n\n"
        f"❓ **Вопрос:** {item['q']}\n\n"
        f"👇 *Кто первым напишет правильный ответ прямо в чат, тот и победил!*",
        parse_mode="Markdown"
    )

# Проверка ответов на викторину в сообщениях чата
@dp.message(~F.text.startswith("/"))
async def check_quiz_answer(message: types.Message):
    chat_id = message.chat.id
    if chat_id not in active_quizzes:
        return

    user_text = message.text.strip().lower()
    correct_answers = active_quizzes[chat_id]

    if any(ans == user_text for ans in correct_answers):
        del active_quizzes[chat_id]
        await message.reply(
            f"🎉 **ПРАВИЛЬНО!** [{message.from_user.first_name}](tg://user?id={message.from_user.id}) дает верный ответ и получает 1 очко!",
            parse_mode="Markdown"
        )


# --- ИГРА 2: КАМЕНЬ-НОЖНИЦЫ-БУМАГА (ДУЭЛЬ НА КНОПКАХ) ---

@dp.message(Command("rps"))
async def cmd_rps(message: types.Message):
    if not message.reply_to_message or message.reply_to_message.from_user.is_bot:
        await message.reply("⚠️ Ответь этой командой на сообщение соперника!")
        return

    p1 = message.from_user
    p2 = message.reply_to_message.from_user

    if p1.id == p2.id:
        await message.reply("Нельзя играть самому с собой!")
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="🪨 Камень", callback_data="rps_move_rock")
    builder.button(text="✂️ Ножницы", callback_data="rps_move_scissors")
    builder.button(text="📄 Бумага", callback_data="rps_move_paper")
    builder.adjust(3)

    msg = await message.answer(
        f"⚔️ **Камень-Ножницы-Бумага!**\n\n"
        f"🎮 Игроки: {p1.first_name} VS {p2.first_name}\n"
        f"👇 Нажмите кнопки ниже, чтобы сделать скрытый ход!",
        reply_markup=builder.as_markup()
    )

    rps_games[msg.message_id] = {
        "p1": p1.id, "p2": p2.id,
        "p1_name": p1.first_name, "p2_name": p2.first_name,
        "p1_move": None, "p2_move": None
    }

@dp.callback_query(F.data.startswith("rps_move_"))
async def handle_rps_move(callback: types.CallbackQuery):
    msg_id = callback.message.message_id
    if msg_id not in rps_games:
        await callback.answer("Эта игра уже завершена!", show_alert=True)
        return

    game = rps_games[msg_id]
    user_id = callback.from_user.id

    if user_id not in [game["p1"], game["p2"]]:
        await callback.answer("Вы не участник этой дуэли!", show_alert=True)
        return

    move = callback.data.replace("rps_move_", "")

    if user_id == game["p1"]:
        if game["p1_move"]:
            await callback.answer("Ты уже сделал ход!", show_alert=True)
            return
        game["p1_move"] = move
    elif user_id == game["p2"]:
        if game["p2_move"]:
            await callback.answer("Ты уже сделал ход!", show_alert=True)
            return
        game["p2_move"] = move

    await callback.answer("Ваш ход принят! 🤫")

    # Если оба сделали ходы — подводим итоги
    if game["p1_move"] and game["p2_move"]:
        m1, m2 = game["p1_move"], game["p2_move"]
        moves_map = {"rock": "🪨 Камень", "scissors": "✂️ Ножницы", "paper": "📄 Бумага"}

        res_text = f"⚔️ **РЕЗУЛЬТАТЫ ИГРЫ:**\n\n"
        res_text += f"👤 {game['p1_name']}: {moves_map[m1]}\n"
        res_text += f"👤 {game['p2_name']}: {moves_map[m2]}\n\n"

        if m1 == m2:
            res_text += "🤝 **Ничья!**"
        elif (m1 == "rock" and m2 == "scissors") or (m1 == "scissors" and m2 == "paper") or (m1 == "paper" and m2 == "rock"):
            res_text += f"🏆 **Победил {game['p1_name']}!**"
        else:
            res_text += f"🏆 **Победил {game['p2_name']}!**"

        await callback.message.edit_text(res_text, parse_mode="Markdown")
        del rps_games[msg_id]


# --- ИГРА 3: КОМАНДНЫЙ «САПЁР» (МИННОЕ ПОЛЕ ДЛЯ ЧАТА) ---

@dp.message(Command("mine"))
async def cmd_mine(message: types.Message):
    """Поле 3x3. На одной из клеток мина!"""
    bomb_index = random.randint(0, 8)
    builder = InlineKeyboardBuilder()

    for i in range(9):
        builder.button(text="❓", callback_data=f"field_{i}_{bomb_index}")
    builder.adjust(3)

    await message.answer(
        "💣 **КОМАНДНЫЙ САПЁР!**\n\n"
        "На поле 3x3 спрятана **одна мина** 💣, а в остальных клетках — золото 🪙!\n"
        "Нажимайте кнопки по очереди. Кто наткнется на мину — проиграл!",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data.startswith("field_"))
async def handle_minefield(callback: types.CallbackQuery):
    _, cell_idx_str, bomb_idx_str = callback.data.split("_")
    cell_idx = int(cell_idx_str)
    bomb_idx = int(bomb_idx_str)
    player_name = callback.from_user.first_name

    if cell_idx == bomb_idx:
        await callback.answer("💥 БУУУМ! ТЫ ВЗОРВАЛСЯ!", show_alert=True)
        await callback.message.edit_text(
            f"💥 **ВЗРЫВ!**\n\n"
            f"💀 Игрок **{player_name}** наступил на мину и подорвал весь отряд!\n"
            f"Игра окончена."
        )
    else:
        await callback.answer("🪙 Безопасно! Найдено золото!")
        # Обновляем клавиатуру, отключая нажатую кнопку
        reply_markup = callback.message.reply_markup
        for row in reply_markup.inline_keyboard:
            for btn in row:
                if btn.callback_data == callback.data:
                    btn.text = "🪙"
                    btn.callback_data = "disabled"
        
        await callback.message.edit_reply_markup(reply_markup=reply_markup)


async def main():
    print("🚀 Коллективный игровой бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
