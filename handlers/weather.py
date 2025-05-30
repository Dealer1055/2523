import cv2
import numpy as np
import os

import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command

from keyboards import start_keyboard, shaharlar_keyboard
from config import API_TOKEN, RAPID_API_KEY, url, host
import requests

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(Command("start"))
async def start_handler(message: Message):
    text = f"""👋 Salom {message.from_user.full_name}!\nOb-havo botiga xush kelibsiz!"""
    await message.answer(text=text, reply_markup=start_keyboard.as_markup())


@dp.callback_query(F.data == "weather")
async def weather_handler(callback: CallbackQuery):
    await callback.message.answer(text="📍 Kerakli shaharni tanlang:", reply_markup=shaharlar_keyboard.as_markup())
    await callback.answer()  # bu callbackni tugatish uchun 


@dp.callback_query(F.data.in_(["tashkent", "andijan", "london", "new_york", "moskva", "tokyo"]))
async def get_weather(callback: CallbackQuery):
    city = callback.data  # tashkent, bo'lishi mumkin qachonki Toshkent inline keyboard bosilganda
    savol = {"city_name": city}

    headers = {
        "x-rapidapi-key": RAPID_API_KEY,
        "x-rapidapi-host": host
    }

    response = requests.get(url, headers=headers, params=savol)
    
    try:
        temp_kelvin = response.json()['main']['temp']
        temp_celsius = round(temp_kelvin - 273.15)
        await callback.message.edit_text(text=f"🌤 {city.upper()} shahrida ob-havo: {temp_celsius}°C")
        await callback.message.answer("🔄 Boshqa shaharni tanlang:", reply_markup=shaharlar_keyboard.as_markup())
    except Exception as e:
        await callback.message.edit_text("❌ Ma'lumot olishda xatolik yuz berdi.")
        await callback.message.answer("🔄 Boshqa shaharni tanlang:", reply_markup=shaharlar_keyboard.as_markup())
        # print("Xato:", e)

    await callback.answer()


@dp.callback_query(F.data == "multik")
async def multik_handler(callback: CallbackQuery):
    await callback.message.answer("📸 Istalgan rasm jo'nating, men sizga multfilm qilib beraman")
    await callback.answer()


@dp.message(F.photo)
async def cartoon_rasm_yuborish(message: Message):
    photo = message.photo[-1]  # Eng sifatli rasm
    file_info = await bot.get_file(photo.file_id)
    file_path = file_info.file_path

    file = await bot.download_file(file_path)
    image_bytes = np.asarray(bytearray(file.read()), dtype=np.uint8)
    img = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    edges = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY, 9, 9
    )

    color = cv2.bilateralFilter(img, 9, 300, 300)
    cartoon = cv2.bitwise_and(color, color, mask=edges)

    cartoon_path = f"cartoon_{photo.file_id}.jpg"
    cv2.imwrite(cartoon_path, cartoon)

    await message.answer_photo(photo=FSInputFile(cartoon_path), caption="🖼 Multfilm style rasm!")
    os.remove(cartoon_path)

    await message.answer("🔄 Boshqa rasm yuboring yoki /start orqali bosh menyuga qayting")

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
