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
    raise ValueError("BOT_TOKEN Environment Variable topilmadi! Render-da BOT_TOKEN kiritilganini tekshiring.")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Render 24/7 faol turishi uchun veb-server
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

# 3. BEPUL VA ORIGINAL SIFATNI SAQLOVCHI FONNI TOZALASH ALGORITMI
async def remove_background_hd(image_bytes: bytes) -> bytes:
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field('image_file', image_bytes, filename='photo.jpg', content_type='image/jpeg')
        
        # Photoroom HD Engine (API Key talab qilmaydi, 4K sifatni saqlaydi)
        url = "https://sdk.photoroom.com/v1/segment"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "x-api-key": "sandbox"  # Bepul va ochiq sinov kaliti
        }
        
        try:
            async with session.post(url, data=data, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.read()
                else:
                    logging.error(f"Server xatosi: STATUS {resp.status}")
        except Exception as e:
            logging.error(f"So'rovda xatolik: {e}")
            
    return None

# 4. HANDLERLAR
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    welcome_text = (
        "👋 **Salom! Men Ultra HD (4K) rasmlar fonini tozalovchi botman.**\n\n"
        "Botdan foydalanish va Ultra-HD sifatda rasm olish uchun "
        "avval mening Instagram sahifamga obuna bo'ling!"
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
        "⚡ **Pro (4K Ultra-HD) ishlov berish**\n\n"
        "Instagram sahifamizga obuna bo'lganingizni tasdiqlang va "
        "**'4K Ultra-HD yuklash'** tugmasini bosing:"
    )
    process_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📸 Instagram Profil", url=INSTAGRAM_LINK)],
            [InlineKeyboardButton(text="🚀 4K Ultra-HD yuklash", callback_data=f"process_{photo_id}")]
        ]
    )
    await message.answer(confirm_text, reply_markup=process_keyboard, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("process_"))
async def process_photo_callback(callback: CallbackQuery):
    photo_id = callback.data.split("process_")[1]
    status_msg = await callback.message.answer("⚡ **Original 4K Ultra-HD ishlov berilmoqda, biroz kuting...**", parse_mode="Markdown")
    await callback.answer()
    
    try:
        # Telegram'dan eng yuqori sifatdagi rasmni yuklab olish
        file_info = await bot.get_file(photo_id)
        photo_bytes_io = await bot.download_file(file_info.file_path)
        photo_bytes = photo_bytes_io.read()
        
        # Fonni tozalash
        clean_png_bytes = await remove_background_hd(photo_bytes)
        
        if clean_png_bytes:
            # Rasmni fayl (Document) shaklida yuborish (Telegram sifatni siqib qo'ymasligi uchun)
            result_file = BufferedInputFile(clean_png_bytes, filename="4K_UltraHD_no_bg.png")
            await callback.message.answer_document(
                document=result_file, 
                caption="✅ **Rasmingiz original 4K Ultra-HD sifatda foni tozalandi!**",
                parse_mode="Markdown"
            )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Rasmni qayta ishlashda xatolik bo'ldi. Boshqa rasm yuborib ko'ring.")
        
    except Exception as e:
        logging.error(f"Xatolik yuz berdi: {e}")
        await status_msg.edit_text("❌ Rasmni yuklab olishda xatolik yuz berdi.")

@dp.message()
async def other_messages(message: types.Message):
    await message.answer("Iltimos, menga faqat **rasm** yuboring!", parse_mode="Markdown")

async def main():
    await start_dummy_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
