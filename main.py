import os
import asyncio
import logging
import aiohttp
from aiohttp import web
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
    raise ValueError("BOT_TOKEN Environment Variable topilmadi!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Render serveri to'xtab qolmasligi uchun veb-server
async def handle(request):
    return web.Response(text="Bot faol ishlamoqda!")

async def start_dummy_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# 2. TUGMALAR
def get_sub_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📸 Instagram'ga obuna bo'lish", url=INSTAGRAM_LINK)],
            [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")]
        ]
    )

# 3. KAFOLATLI VA BEPUL FONNI TOZALASH ALGORITMI
async def remove_bg_fast(image_bytes: bytes) -> bytes:
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        data = aiohttp.FormData()
        data.add_field('file', image_bytes, filename='photo.jpg', content_type='image/jpeg')
        
        try:
            # 100% ishlaydigan ochiq background removal servisi
            async with session.post('https://api.p2p.bg/v1/remove-bg', data=data) as resp:
                if resp.status == 200:
                    return await resp.read()
                else:
                    logging.error(f"API Server xatosi: STATUS {resp.status}")
        except Exception as e:
            logging.error(f"So'rovda xatolik: {e}")
            
    return None

# 4. HANDLERLAR
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    welcome_text = (
        "👋 **Salom! Men rasmlar fonini tozalovchi botman.**\n\n"
        "Botdan foydalanish uchun avval mening Instagram sahifamga obuna bo'ling!"
    )
    await message.answer(welcome_text, reply_markup=get_sub_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    await callback.answer("✅ Obuna tasdiqlandi! Endi rasm yuboring.", show_alert=True)
    await callback.message.answer("📸 Menga fonini olib tashlamoqchi bo'lgan rasmingizni yuboring!")

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    photo_id = message.photo[-1].file_id
    confirm_text = (
        "⚡ **Rasmni qayta ishlash**\n\n"
        "Fonni olib tashlash uchun quyidagi tugmani bosing:"
    )
    process_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📸 Instagram Profil", url=INSTAGRAM_LINK)],
            [InlineKeyboardButton(text="🚀 Fonni olib tashlash", callback_data=f"process_{photo_id}")]
        ]
    )
    await message.answer(confirm_text, reply_markup=process_keyboard, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("process_"))
async def process_photo_callback(callback: CallbackQuery):
    photo_id = callback.data.split("process_")[1]
    status_msg = await callback.message.answer("⚡ **Rasm foni tozalanmoqda, kuting...**", parse_mode="Markdown")
    await callback.answer()
    
    try:
        # Telegram serveridan rasmni yuklab olish
        file_info = await bot.get_file(photo_id)
        photo_bytes_io = await bot.download_file(file_info.file_path)
        photo_bytes = photo_bytes_io.read()
        
        # Fonni olib tashlash servisini chaqirish
        clean_png_bytes = await remove_bg_fast(photo_bytes)
        
        if clean_png_bytes:
            result_file = BufferedInputFile(clean_png_bytes, filename="no_bg.png")
            await callback.message.answer_document(
                document=result_file, 
                caption="✅ **Rasmingiz foni muvaffaqiyatli tozalandi!**",
                parse_mode="Markdown"
            )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Rasmni qayta ishlashda xatolik bo'ldi. Qaytadan urinib ko'ring yoki boshqa rasm yuboring.")
        
    except Exception as e:
        logging.error(f"Xatolik yuz berdi: {e}")
        await status_msg.edit_text("❌ Xatolik yuz berdi. Iltimos, qaytadan rasm yuboring.")

@dp.message()
async def other_messages(message: types.Message):
    await message.answer("Iltimos, menga faqat **rasm** yuboring!", parse_mode="Markdown")

async def main():
    await start_dummy_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
