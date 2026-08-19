import os
import io
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import (
    BufferedInputFile, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery
)
from rembg import remove, new_session
from PIL import Image

# 1. BOT SOZLAMALARI
BOT_TOKEN = os.getenv("BOT_TOKEN")
INSTAGRAM_LINK = "https://www.instagram.com/murodovvv_686"  # Profil havolangiz

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Yuqori tezlik va sifat uchun rembg modelini xotiraga tayyorlab qo'yamiz (u2net)
session = new_session("u2net")
# Tezlikni oshirish uchun fonda ishlovchi potoklar puli
executor = ThreadPoolExecutor(max_workers=4)

# Render serveri to'xtab qolmasligi uchun kichik veb-server
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

# 2. TUGMALAR (KEYBOARD) MANTIQLARI
def get_sub_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📸 Instagram'ga obuna bo'lish", url=INSTAGRAM_LINK)
            ],
            [
                InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")
            ]
        ]
    )
    return keyboard

# 3. RASMNI PRO DARAJADA ISHLASH (OG'IR AMAL)
def process_image_hd(image_bytes: bytes) -> bytes:
    # Original rasmni ochamiz
    input_image = Image.open(io.BytesIO(image_bytes))
    
    # rembg orqali maksimal sifatda (u2net) fonni tozalash
    output_image = remove(input_image, session=session)
    
    # Ultra-HD formatda PNG xotirasiga saqlash
    output_buffer = io.BytesIO()
    output_image.save(output_buffer, format="PNG", optimize=True, quality=100)
    output_buffer.seek(0)
    return output_buffer.read()

# 4. BOT BUYRUKLARI VA ISHLOVCHILARI

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    welcome_text = (
        "👋 **Salom! Men Pro darajadagi rasmlar fonini tozalovchi botman.**\n\n"
        "Botdan foydalanish va Ultra-HD sifatda rasm olish uchun "
        "avval mening Instagram sahifamga obuna bo'ling!"
    )
    await message.answer(welcome_text, reply_markup=get_sub_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    await callback.answer("✅ Obuna tasdiqlandi! Endi menga rasm yuborishingiz mumkin.", show_alert=True)
    await callback.message.answer("📸 Menga fonini olib tashlamoqchi bo'lgan rasmingizni yuboring!")

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    # Har gal rasm yuborilganda obunani qayta so'rash/eslatish mexanizmi
    confirm_text = (
        "⚡ **Pro Sifatda ishlov berish**\n\n"
        "Instagram sahifamizga obuna bo'lganingizni tasdiqlang va "
        "**'A'lo sifatda yuklash'** tugmasini bosing:"
    )
    
    # Rasm file_id'sini saqlab tugmaga biriktiramiz
    photo_id = message.photo[-1].file_id
    process_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📸 Instagram Profil", url=INSTAGRAM_LINK)],
            [InlineKeyboardButton(text="🚀 A'lo sifatda yuklash", callback_data=f"process_{photo_id}")]
        ]
    )
    await message.answer(confirm_text, reply_markup=process_keyboard, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("process_"))
async def process_photo_callback(callback: CallbackQuery):
    photo_id = callback.data.split("process_")[1]
    
    status_msg = await callback.message.answer("⚡ **Ultra-HD ishlov berilmoqda, biroz kuting...**", parse_mode="Markdown")
    await callback.answer()
    
    try:
        # Rasmni Telegram serveridan tezkor yuklab olish
        file_info = await bot.get_file(photo_id)
        photo_bytes = await bot.download_file(file_info.file_path)
        
        # Asinxron xronologiyani buzmaslik uchun og'ir vazifani alohida potokda bajaramiz (Maksimal tezlik)
        loop = asyncio.get_event_loop()
        clean_png_bytes = await loop.run_in_executor(
            executor, process_image_hd, photo_bytes.read()
        )
        
        # Tayyor sifatli rasmni Hujjat (Document) ko'rinishida yuborish (Sifat yo'qolmasligi uchun)
        result_file = BufferedInputFile(clean_png_bytes, filename="pro_no_bg.png")
        await callback.message.answer_document(
            document=result_file, 
            caption="✅ **Rasmingiz Pro (Ultra-HD) sifatda foni tozalandi!**",
            parse_mode="Markdown"
        )
        await status_msg.delete()
        
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await status_msg.edit_text("❌ Rasmni qayta ishlashda xatolik yuz berdi. Qaytadan urinib ko'ring.")

@dp.message()
async def other_messages(message: types.Message):
    await message.answer("Iltimos, menga faqat **rasm** yuboring!", parse_mode="Markdown")

# 5. MAIN ISHGA TUSHIRISH
async def main():
    await start_dummy_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
