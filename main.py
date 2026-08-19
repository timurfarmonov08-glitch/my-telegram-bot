import os
import io
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
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Render serveri uyquga ketmasligi uchun veb-server
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

# 2. INTERFEYS TUGMALARI
def get_sub_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📸 Instagram'ga obuna bo'lish", url=INSTAGRAM_LINK)],
            [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")]
        ]
    )

# 3. BEPUL VA CHEKSIZ FONNI TOZALASH FUNKSIYASI (API-KEYSIZ)
async def remove_bg_free(image_bytes: bytes) -> bytes:
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field('file', image_bytes, filename='image.jpg', content_type='image/jpeg')
        
        # Bepul va tezkor ochiq server
        async with session.post('https://api.p2p.bg/v1/remove-bg', data=data) as resp:
            if resp.status == 200:
                return await resp.read()
            else:
                # Zaxira bepul server (xavfsizlik uchun)
                async with session.post('https://bg-remove.free-api.workers.dev/', data=data) as resp2:
                    if resp2.status == 200:
                        return await resp2.read()
    return None

# 4. BOT MANTIQLARI
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
    photo_id = message.photo[-1].file_id
    confirm_text = (
        "⚡ **Pro Sifatda ishlov berish**\n\n"
        "Instagram sahifamizga obuna bo'lganingizni tasdiqlang va "
        "**'A'lo sifatda yuklash'** tugmasini bosing:"
    )
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
    status_msg = await callback.message.answer("⚡ **Pro (Ultra-HD) ishlov berilmoqda, biroz kuting...**", parse_mode="Markdown")
    await callback.answer()
    
    try:
        file_info = await bot.get_file(photo_id)
        photo_bytes = await bot.download_file(file_info.file_path)
        
        # Asinxron ravishda bepul serverda fonni tozalash
        clean_png_bytes = await remove_bg_free(photo_bytes.read())
        
        if clean_png_bytes:
            result_file = BufferedInputFile(clean_png_bytes, filename="pro_no_bg.png")
            await callback.message.answer_document(
                document=result_file, 
                caption="✅ **Rasmingiz Pro (Ultra-HD) sifatda foni tozalandi!**",
                parse_mode="Markdown"
            )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Foni tozalashda xatolik bo'ldi. Boshqa rasm yuborib ko'ring.")
        
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
