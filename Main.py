import asyncio
import logging
import os
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# --- НАСТРОЙКИ ТОКЕНА ---
# Берём токен из Environment Variables на Render. Если локально — подставит fallback.
BOT_TOKEN = "8862473984:AAFrlUGDAjDn4wb_QDHV8_xI9MTqjCbHiNg" 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN.strip())  # strip() защищает от случайных пробелов
dp = Dispatcher()

# --- ВЕБ-СЕРВЕР ДЛЯ БЕСПЛАТНОГО ТАРИФА RENDER (WEB SERVICE) ---
async def handle_ping(request):
    return web.Response(text="Bot is live and running!")

async def start_web_server():
    """Запускает фейковый веб-порт, который ищет Render"""
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render автоматически передаёт порт через переменную PORT
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Веб-сервер успешно запущен на порту {port}")

# --- ХРАНИЛИЩА СОСТОЯНИЙ ИГР ---
active_quizzes = {}  # {chat_id: ["ответ1", "ответ2"]}
rps_games = {}       # {msg_id: game_data}

# База вопросов для викторины
QUIZ_QUESTIONS = [
    {"q": "В какой игре главный герой — Геральт из Ривии?", "a": ["ведьмак", "thewitcher", "witcher"]},
    {"q": "Какая компания создала консоль PlayStation?", "a": ["sony", "сони"]},
    {"q": "Как называется популярный песочный мир из кубов?", "a": ["minecraft", "майнкрафт"]},
    {"q": "В каком году вышла игра GTA V?", "a": ["2013"]},
    {"q": "Как зовут водопроводчика в красной кепке из игр Nintendo?", "a": ["марио", "mario"]},
    {"q": "Как называется гоночная серия игр от Microsoft?", "a": ["forza", "forza horizon"]},
]

# --- КОМАНДА /START И ПОМОЩЬ ---
@dp.message(Command("start", "help"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🎮 **Игровой Бот для Групповых Чатов!**\n\n"
        "**Команды для игр:**\n"
        "• `/quiz` — запустить викторину на скорость для всего чата 🧠\n"
        "• `/rps` (ответом на сообщение) — дуэль в Камень-Ножницы-Бумага ✂️\n"
        "• `/mine` — командный Сапёр / Минное поле 💣",
        parse_mode="Markdown"
    )

# --- ИГРА 1: ВИКТОРИНА ---
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    chat_id = message.chat.id
    if chat_id in active_quizzes:
        await message.reply("⚠️ В чате уже идет викторина! Напишите ответ на текущий вопрос.")
        return

    item = random.choice(QUIZ_QUESTIONS)
    active_quizzes[chat_id] = item["a"]

    await message.answer(
        f"🧠 **ВИКТОРИНА!**\n\n"
        f"❓ **Вопрос:** {item['q']}\n\n"
        f"👇 *Кто первым напишет правильный ответ в чат — побеждает!*",
        parse_mode="Markdown"
    )

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
            f"🎉 **ПРАВИЛЬНО!** [{message.from_user.first_name}](tg://user?id={message.from_user.id}) дает верный ответ!",
            parse_mode="Markdown"
        )

# --- ИГРА 2: КАМЕНЬ-НОЖНИЦЫ-БУМАГА ---
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
    builder.button(text="🪨 Камень", callback_data="rps_rock")
    builder.button(text="✂️ Ножницы", callback_data="rps_scissors")
    builder.button(text="📄 Бумага", callback_data="rps_paper")
    builder.adjust(3)

    msg = await message.answer(
        f"⚔️ **Камень-Ножницы-Бумага!**\n\n"
        f"🎮 Игроки: {p1.first_name} VS {p2.first_name}\n"
        f"👇 Сделайте скрытый ход кнопками ниже:",
        reply_markup=builder.as_markup()
    )

    rps_games[msg.message_id] = {
        "p1": p1.id, "p2": p2.id,
        "p1_name": p1.first_name, "p2_name": p2.first_name,
        "p1_move": None, "p2_move": None
    }

@dp.callback_query(F.data.startswith("rps_"))
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

    move = callback.data.replace("rps_", "")

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

# --- ИГРА 3: МИННОЕ ПОЛЕ ---
@dp.message(Command("mine"))
async def cmd_mine(message: types.Message):
    bomb_index = random.randint(0, 8)
    builder = InlineKeyboardBuilder()

    for i in range(9):
        builder.button(text="❓", callback_data=f"field_{i}_{bomb_index}")
    builder.adjust(3)

    await message.answer(
        "💣 **КОМАНДНЫЙ САПЁР!**\n\n"
        "На поле спрятана **одна мина** 💣!\n"
        "Нажимайте кнопки по очереди. Кто наступит на мину — подорвётся!",
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
            f"💥 **ВЗРЫВ!**\n\n💀 Игрок **{player_name}** наступил на мину! Игра окончена."
        )
    else:
        await callback.answer("🪙 Безопасно!")
        reply_markup = callback.message.reply_markup
        for row in reply_markup.inline_keyboard:
            for btn in row:
                if btn.callback_data == callback.data:
                    btn.text = "🪙"
                    btn.callback_data = "disabled"
        await callback.message.edit_reply_markup(reply_markup=reply_markup)

# --- ТОЧКА ВХОДА ---
async def main():
    # 1. Запускаем фейк-вебсервер для удовлетворения проверок Render Web Service
    await start_web_server()
    
    # 2. Запуск бота
    print("🚀 Игровой бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
 
