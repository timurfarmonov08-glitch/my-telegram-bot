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

# 1. SOZLAMALAR
BOT_TOKEN = os.getenv("BOT_TOKEN")
REMOVE_BG_API_KEY = os.getenv("REMOVE_BG_API_KEY")
INSTAGRAM_LINK = "https://www.instagram.com/murodovvv_686"

logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Render to'xtab qolmasligi uchun veb-server
async def handle(request):
    return web.Response(text="Bot ishlayapti!")

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

# 3. 4K REMOVE.BG FUNKSIYASI
async def remove_bg_hd(image_bytes: bytes) -> bytes:
    if not REMOVE_BG_API_KEY:
        logging.error("REMOVE_BG_API_KEY kiritilmagan!")
        return None
        
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        data = aiohttp.FormData()
        data.add_field('image_file', image_bytes, filename='photo.jpg', content_type='image/jpeg')
        data.add_field('size', 'full')  # Original 4K HD o'lcham
        
        headers = {'X-Api-Key': REMOVE_BG_API_KEY}
        
        try:
            async with session.post('https://api.remove.bg/v1.0/removebg', data=data, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.read()
                else:
                    err = await resp.text()
                    logging.error(f"Remove.bg Xatosi [{resp.status}]: {err}")
        except Exception as e:
            logging.error(f"So'rovda xatolik: {e}")
            
    return None

# 4. BOT BUYRUQLARI
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    welcome_text = (
        "👋 **Salom! Men rasmlar fonini Ultra HD (4K) sifatda tozalovchi botman.**\n\n"
        "Botdan foydalanish uchun avval Instagram sahifamizga obuna bo'ling!"
    )
    await message.answer(welcome_text, reply_markup=get_sub_keyboard(), parse_mode="Markdown")

# Obunani tekshirish (ESKI XABARNI O'CHIRADI)
@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    await callback.answer("✅ Obuna tasdiqlandi!", show_alert=True)
    
    # Eski obuna so'ragan xabarni tugmalari bilan birga o'chirib tashlaymiz
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning(f"Xabarni o'chirishda xatlik: {e}")
        
    await callback.message.answer("📸 **Ajoyib! Endi menga fonini olib tashlamoqchi bo'lgan rasmingizni yuboring.**", parse_mode="Markdown")

# Rasm kelganda avtomatik ishlov berish
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    # Yuklanayotgani haqida habar beramiz
    status_msg = await message.answer("⚡ **Rasm foni 4K Ultra-HD sifatda tozalanmoqda, kuting...**", parse_mode="Markdown")
    
    try:
        # Eng katta sifatdagi rasmni olamiz
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        photo_bytes_io = await bot.download_file(file_info.file_path)
        photo_bytes = photo_bytes_io.read()
        
        # Fonini tozalaymiz
        clean_png_bytes = await remove_bg_hd(photo_bytes)
        
        if clean_png_bytes:
            # Telegram sifatni siqmasligi uchun hujjat (document) ko'rinishida yuboramiz
            result_file = BufferedInputFile(clean_png_bytes, filename="4K_no_bg.png")
            await message.answer_document(
                document=result_file, 
                caption="✅ **Rasmingiz foni ideal va 4K sifatda tozalandi!**",
                parse_mode="Markdown"
            )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ API bilan bog'lanishda xatolik bo'ldi. Render'da API kalit kiritilganini tekshiring.")
            
    except Exception as e:
        logging.error(f"Xatolik yuz berdi: {e}")
        await status_msg.edit_text("❌ Rasmni qayta ishlashda xatolik bo'ldi.")

@dp.message()
async def other_messages(message: types.Message):
    await message.answer("Iltimos, menga faqat **rasm** yuboring!", parse_mode="Markdown")

async def main():
    await start_dummy_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
