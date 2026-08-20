import os
import io
import asyncio
import logging
from aiohttp import web
from PIL import Image
from rembg import remove
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

# Render serveri to'xtab qolmasligi uchun dummy server
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

# 2. TUGMA
def get_sub_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📸 Instagram'ga obuna bo'lish", url=INSTAGRAM_LINK)],
            [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")]
        ]
    )

# 3. BEPUL VA CHEKLOWSIZ FONNI O'CHIRISH FUNKSIYASI (rembg)
def process_remove_bg(image_bytes: bytes) -> bytes:
    input_image = Image.open(io.BytesIO(image_bytes))
    output_image = remove(input_image)
    
    output_io = io.BytesIO()
    output_image.save(output_io, format='PNG')
    return output_io.getvalue()

# 4. HANDLERLAR
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    welcome_text = (
        "👋 **Salom! Men rasmlar fonini tozalovchi botman.**\n\n"
        "Botdan foydalanish uchun avval Instagram sahifamizga obuna bo'ling!"
    )
    await message.answer(welcome_text, reply_markup=get_sub_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    await callback.answer("✅ Obuna tasdiqlandi!", show_alert=True)
    
    # Eski obuna so'ragan xabarni va tugmalarni o'chirish
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning(f"Xabarni o'chirishda xatolik: {e}")
        
    await callback.message.answer("📸 **Ajoyib! Endi menga fonini olib tashlamoqchi bo'lgan rasmingizni yuboring.**", parse_mode="Markdown")

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    status_msg = await message.answer("⚡ **Rasm foni tozalanmoqda, biroz kuting...**", parse_mode="Markdown")
    
    try:
        # Telegram serveridan rasmni yuklab olish
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        photo_bytes_io = await bot.download_file(file_info.file_path)
        photo_bytes = photo_bytes_io.read()
        
        # Async rejimda rembg kutubxonasini ishlatish
        loop = asyncio.get_event_loop()
        clean_png_bytes = await loop.run_in_executor(None, process_remove_bg, photo_bytes)
        
        if clean_png_bytes:
            result_file = BufferedInputFile(clean_png_bytes, filename="no_bg.png")
            await message.answer_document(
                document=result_file, 
                caption="✅ **Rasmingiz foni muvaffaqiyatli tozalandi!**",
                parse_mode="Markdown"
            )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Rasmni qayta ishlashda xatolik yuz berdi.")
            
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await status_msg.edit_text("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")

@dp.message()
async def other_messages(message: types.Message):
    await message.answer("Iltimos, menga faqat **rasm** yuboring!", parse_mode="Markdown")

async def main():
    await start_dummy_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
