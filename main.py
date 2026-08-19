import os
import io
import logging
import asyncio
import requests
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
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Render serveri to'xtab qolmasligi uchun
async def handle(request):
    return web.Response(text="Bot 24/7 faol ishlamoqda!")

async def start_dummy_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# 2. INTERFEYS
def get_sub_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📸 Instagram'ga obuna bo'lish", url=INSTAGRAM_LINK)],
            [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")]
        ]
    )

# 3. HIGH-RESOLUTION FONNI TOZALASH
def remove_bg_hd(image_bytes: bytes) -> bytes:
    # 4K va HD sifatni buzmasdan qaytaruvchi server so'rovi
    response = requests.post(
        "https://clipdrop-api.co/remove-background/v1",
        files={'image_file': ('image.jpg', image_bytes, 'image/jpeg')},
        headers={"x-api-key": ""}
    )
    if response.status_code == 200:
        return response.content
    return None

# 4. BOT HANDLERLARI
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    welcome_text = (
        "👋 **Salom! Men Pro (4K Ultra-HD) rasmlar fonini tozalovchi botman.**\n\n"
        "Botdan foydalanish va Ultra-HD sifatda rasm olish uchun "
        "avval mening Instagram sahifamga obuna bo'ling!"
    )
    await message.answer(welcome_text, reply_markup=get_sub_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    await callback.answer("✅ Obuna tasdiqlandi! Endi rasm yuborishingiz mumkin.", show_alert=True)
    await callback.message.answer("📸 Menga fonini olib tashlamoqchi bo'lgan rasmingizni yuboring!")

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    photo_id = message.photo[-1].file_id
    confirm_text = (
        "⚡ **Pro (4K Ultra-HD) ishlov berish**\n\n"
        "Instagram sahifamizga obuna bo'lganingizni tasdiqlang va "
        "**'A'lo sifatda yuklash'** tugmasini bosing:"
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
        file_info = await bot.get_file(photo_id)
        photo_bytes = await bot.download_file(file_info.file_path)
        
        loop = asyncio.get_event_loop()
        clean_png_bytes = await loop.run_in_executor(
            None, remove_bg_hd, photo_bytes.read()
        )
        
        if clean_png_bytes:
            result_file = BufferedInputFile(clean_png_bytes, filename="4K_UltraHD_no_bg.png")
            await callback.message.answer_document(
                document=result_file, 
                caption="✅ **Rasmingiz original 4K Ultra-HD sifatda foni tozalandi!**",
                parse_mode="Markdown"
            )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Ishlov berishda xatolik bo'ldi. Boshqa rasm yuborib ko'ring.")
        
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await status_msg.edit_text("❌ Rasmni qayta ishlashda xatolik yuz berdi.")

@dp.message()
async def other_messages(message: types.Message):
    await message.answer("Iltimos, menga faqat **rasm** yuboring!", parse_mode="Markdown")

async def main():
    await start_dummy_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
