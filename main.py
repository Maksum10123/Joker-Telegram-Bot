import asyncio
import logging
import os, random
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from config import BOT_TOKEN, GIPHY_API_KEY

# Конфиг

# Бот будет спать случайное время между этими числами перед отправкой
# Пиши в секундах
MIN_WAIT = 43200
MAX_WAIT = 86400

VOICE_FOLDER = "voices"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

active_loops = set()

async def get_random_joker_gif():
    url = f"https://api.giphy.com/v1/gifs/random?api_key={GIPHY_API_KEY}&tag=joker-Batman"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['data']['images']['original']['url']
    except Exception as e:
        logging.error({e})
    return None


async def random_gif_worker(chat_id):
    logging.info(f"Запущен цикл для чата {chat_id}")

    while chat_id in active_loops:
        wait_time = random.randint(MIN_WAIT, MAX_WAIT)
        logging.info(f"Подождите {wait_time} секунд для отправки Джокера в {chat_id}")

        await asyncio.sleep(wait_time)

        if chat_id in active_loops:
            gif_url = await get_random_joker_gif()
            if gif_url:
                try:
                    await bot.send_animation(chat_id, gif_url)
                except Exception as e:
                    logging.error(f"Не удалось отправить сообщение: {e}")
                    # Если бот заблокирован или кикнут вычёркиваем чат айди из списка
                    active_loops.discard(chat_id)
            else:
                logging.error("ошибка API.")

@dp.message(Command("wake_up_joker"))
async def cmd_start(message: types.Message):
    chat_id = message.chat.id

    if chat_id not in active_loops:
        active_loops.add(chat_id)
        await message.answer("Джокер проснулся. Гифки будут отправляться от выставленного в конфиге времени.")
        # Запускаем фоновую задачу
        asyncio.create_task(random_gif_worker(chat_id))
    else:
        await message.answer("ДЖОКЕР УЖЕ ЗАПУЩЕН")


@dp.message(Command("joker_sleep"))
async def cmd_stop(message: types.Message):
    chat_id = message.chat.id
    if chat_id in active_loops:
        active_loops.discard(chat_id)
        await message.answer("Джокер уснул. Скукотища.")
    else:
        await message.answer_animation("https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExcW5hMGFwOWVyMmZnZjhtbXVmbmdpN29mODNhYjdyNmIwZXRraDJteCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/A363LZlQaX0ZO/giphy.gif")

@dp.message(Command("shytka"))
async def cmd_shytka(message: types.Message):
    try:
        random_filename = random.choice(os.listdir(VOICE_FOLDER))
        voice_path = os.path.join(VOICE_FOLDER, random_filename)
        voice_to_send = FSInputFile(voice_path)

        await message.answer_voice(voice_to_send)
    except Exception as e:
        logging.error({e})

@dp.message(Command("random"))
async def cmd_random(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Казик", callback_data="send_kazino")],
        [InlineKeyboardButton(text="Кубик", callback_data="send_cube")],
        [InlineKeyboardButton(text="Рональдо", callback_data="send_ronaldo")],
        [InlineKeyboardButton(text="Дартс", callback_data="send_dartz")]
    ])
    await message.answer("Выбери Игру:", reply_markup=keyboard)


@dp.callback_query(F.data.in_({"send_kazino", "send_cube", "send_ronaldo", "send_dartz"}))
async def play_games_handler(callback: types.CallbackQuery):
    games_map = {
        "send_kazino": "🎰",
        "send_cube": "🎲",
        "send_ronaldo": "⚽",
        "send_dartz": "🎯"
    }

    selected_emoji = games_map[callback.data]

    await callback.message.answer_dice(emoji=selected_emoji)
    await callback.message.delete()


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Мой GitHub", url="https://github.com/Maksum10123")],
        [InlineKeyboardButton(text="📂 Репозиторий проекта", url="https://github.com/Maksum10123/Joker-Telegram-Bot")]
    ])

    text = (
        "<b>Привет! Это простой бот про Джокера.</b>\n\n"
        "Сделан потому что у моего друга был не рабочий бот и бла-бла-бла...\n"
        "Спасибо Aiogram за  удобную библиотеку"
    )

    await message.reply(text, parse_mode="HTML", reply_markup=keyboard)



async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
