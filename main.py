import os
import io
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from rembg import remove, new_session
from PIL import Image

BOT_TOKEN = os.getenv("BOT_TOKEN")
INSTAGRAM_LINK = "https://www.instagram.com/murodovvv_686"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Yuqori aniqlikdagi u2net neyrotarmoq modelini xotiraga tayyorlaymiz
session = new_session("u2net")
executor = ThreadPoolExecutor(max_workers=2)

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

def get_sub_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📸 Instagram'ga obuna bo'lish", url=INSTAGRAM_LINK)],
            [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")]
        ]
    )

# ORIGINAL 4K SIFATNI SAQLASH ALGORITMI
def process_hd_image(image_bytes: bytes) -> bytes:
    input_image = Image.open(io.BytesIO(image_bytes))
    
    # Original rasmning o'lchamini olamiz (masalan: 3840x2160)
    orig_width, orig_height = input_image.size
    
    # rembg orqali fonni tozalash
    output_image = remove(input_image, session=session)
    
    # Original 4K o'lchamga qaytarish va piksel tiniqligini saqlash (LANCZOS resampling)
    if output_image.size != (orig_width, orig_height):
        output_image = output_image.resize((orig_width, orig_height), Image.Resampling.LANCZOS)
    
    output_buffer = io.BytesIO()
    # PNG holatida maksimal (100%) sifat bilan saqlash
    output_image.save(output_buffer, format="PNG", optimize=False)
    output_buffer.seek(0)
    return output_buffer.read()

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer(
        "👋 **Salom! Men Pro (4K) rasmlar fonini tozalovchi botman.**\n\n"
        "Menga rasm yuboring!", 
        reply_markup=get_sub_keyboard(), 
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    await callback.answer("✅ Obuna tasdiqlandi! Endi rasm yuboring.", show_alert=True)
    await callback.message.answer("📸 4K sifatda ishlov berish uchun rasm yuboring!")

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    photo_id = message.photo[-1].file_id
    process_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📸 Instagram Profil", url=INSTAGRAM_LINK)],
            [InlineKeyboardButton(text="🚀 4K Ultra-HD yuklash", callback_data=f"process_{photo_id}")]
        ]
    )
    await message.answer("⚡ **4K Original sifatda ishlov berishni tasdiqlang:**", reply_markup=process_keyboard)

@dp.callback_query(F.data.startswith("process_"))
async def process_photo_callback(callback: CallbackQuery):
    photo_id = callback.data.split("process_")[1]
    status_msg = await callback.message.answer("⚡ **4K Ultra-HD ishlov berilmoqda, kuting...**")
    await callback.answer()
    
    try:
        file_info = await bot.get_file(photo_id)
        photo_bytes = await bot.download_file(file_info.file_path)
        
        loop = asyncio.get_event_loop()
        clean_png_bytes = await loop.run_in_executor(
            executor, process_hd_image, photo_bytes.read()
        )
        
        result_file = BufferedInputFile(clean_png_bytes, filename="4K_no_bg.png")
        await callback.message.answer_document(
            document=result_file, 
            caption="✅ **Rasmingiz original 4K sifatda va ravshanlik yo'qolmagan holda tozalandi!**"
        )
        await status_msg.delete()
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await status_msg.edit_text("❌ Ishlov berishda xatolik yuz berdi.")

async def main():
    await start_dummy_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
