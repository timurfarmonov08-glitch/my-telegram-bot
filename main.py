import os
import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import (
    BufferedInputFile, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery
)

# 1. BOT SOZLAMALARI
BOT_TOKEN = os.getenv("BOT_TOKEN")
INSTAGRAM_LINK = "https://www.instagram.com/murodovvv_686"

logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 2. INSTAGRAM OBUNA TUGMASI
def get_sub_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📸 Instagram'ga obuna bo'lish", url=INSTAGRAM_LINK)],
            [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")]
        ]
    )

# 3. YENGIL VA BEPUL FONNI O'CHIRISH (API key shart emas)
async def remove_bg_fast(image_bytes: bytes) -> bytes:
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        data = aiohttp.FormData()
        data.add_field('image_file', image_bytes, filename='photo.jpg', content_type='image/jpeg')
        
        url = "https://sdk.photoroom.com/v1/segment"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "x-api-key": "sandbox"
        }
        
        try:
            async with session.post(url, data=data, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.read()
                else:
                    logging.error(f"API xatosi: STATUS {resp.status}")
        except Exception as e:
            logging.error(f"So'rovda xatolik: {e}")
            
    return None

# 4. BOT BUYRUQLARI
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    welcome_text = (
        "👋 **Salom! Men rasmlar fonini tozalovchi botman.**\n\n"
        "Botdan foydalanish uchun avval Instagram sahifamizga obuna bo'ling!"
    )
    await message.answer(welcome_text, reply_markup=get_sub_keyboard(), parse_mode="Markdown")

# Obuna tekshirilganda eski yozuvni O'CHIRIB TASHASH
@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    await callback.answer("✅ Obuna tasdiqlandi!", show_alert=True)
    
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning(f"Xabarni o'chirishda xatolik: {e}")
        
    await callback.message.answer("📸 **Ajoyib! Endi menga fonini olib tashlamoqchi bo'lgan rasmingizni yuboring.**", parse_mode="Markdown")

# Rasm kelganda avtomatik ishlash
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    status_msg = await message.answer("⚡ **Rasm foni tozalanmoqda, biroz kuting...**", parse_mode="Markdown")
    
    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        photo_bytes_io = await bot.download_file(file_info.file_path)
        photo_bytes = photo_bytes_io.read()
        
        clean_png_bytes = await remove_bg_fast(photo_bytes)
        
        if clean_png_bytes:
            result_file = BufferedInputFile(clean_png_bytes, filename="no_bg.png")
            await message.answer_document(
                document=result_file, 
                caption="✅ **Rasmingiz foni muvaffaqiyatli tozalandi!**",
                parse_mode="Markdown"
            )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Rasmni qayta ishlashda xatolik bo'ldi. Qaytadan urinib ko'ring.")
            
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await status_msg.edit_text("❌ Xatolik yuz berdi.")

@dp.message()
async def other_messages(message: types.Message):
    await message.answer("Iltimos, menga faqat **rasm** yuboring!", parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
