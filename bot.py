import os, logging, asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
import google.generativeai as genai
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8672975647:AAHpWG5xTxLRv0IKKy6tvl_VlAn_FfL99vM")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDRJLp8JGpKid1pTJBRVgeumPdObveAXwY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Simple dict for sessions - no FSM
sessions = {}

PROMPTS = {
    "restaurant": "Ты AI-ассистент ресторана 'Bella Italia'. Принимаешь бронирования столиков, рассказываешь о меню. Меню: Паста Карбонара - 25₾, Пицца Маргарита - 20₾, Тирамису - 12₾. Время: 11:00-23:00. Адрес: Тбилиси, ул. Руставели 15. Будь дружелюбным. НЕ переводи на менеджера - ты сам всё решаешь. Определи язык клиента и отвечай на нём.",
    "salon": "Ты AI-ассистент салона красоты 'Beauty Studio'. Записываешь на процедуры. Услуги: Женская стрижка - 80₾, Маникюр - 60₾, Массаж лица - 120₾. График: 9:00-21:00. Адрес: Тбилиси, ул. Пекина 10. Будь заботливым. НЕ переводи на менеджера. Определи язык клиента и отвечай на нём.",
    "delivery": "Ты AI-ассистент службы доставки 'FastCargo'. Принимаешь заявки. Тарифы: По городу до 5кг - 12₾, За город до 10кг - 30₾, Экспресс - 22₾. Доставка 1-3 дня. Будь чётким. НЕ переводи на менеджера. Определи язык клиента и отвечай на нём.",
    "hotel": "Ты AI-ассистент отеля 'Grand Plaza'. Бронируешь номера. Стандарт - 150₾/ночь, Люкс - 300₾/ночь. SPA, фитнес, завтрак включён. Адрес: Батуми, набережная 5. Будь гостеприимным. НЕ переводи на менеджера. Определи язык клиента и отвечай на нём.",
    "fitness": "Ты AI-ассистент фитнес-клуба 'PowerGym'. Записываешь на тренировки. Абонементы: 1 мес - 120₾, 6 мес - 600₾, год - 1000₾. Зал, бассейн, групповые, тренер. Режим: 6:00-23:00. Будь мотивирующим. НЕ переводи на менеджера. Определи язык клиента и отвечай на нём.",
    "other": "Ты универсальный AI-ассистент для бизнеса. Помогаешь клиентам, принимаешь заявки, консультируешь. Будь полезным. НЕ переводи на менеджера. Определи язык клиента и отвечай на нём."
}

NICHE_NAMES = {"restaurant": "🍕 Ресторан", "salon": "💇 Салон красоты", "delivery": "🚚 Доставка", "hotel": "🏨 Отель", "fitness": "🏋️ Фитнес", "other": "💼 Другое"}

CTA = "\n\n━━━━━━━━━━━━━━━\n✨ *Понравилось?*\n\n🚀 Мы можем настроить такого же AI-ассистента для ВАШЕГО бизнеса за 24 часа!\n\n👉 Узнать подробнее: @ai_centers_hub_bot\n💰 От $15/мес"

def get_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍕 Ресторан", callback_data="n_restaurant"),
         InlineKeyboardButton(text="💇 Салон красоты", callback_data="n_salon")],
        [InlineKeyboardButton(text="🚚 Доставка", callback_data="n_delivery"),
         InlineKeyboardButton(text="🏨 Отель", callback_data="n_hotel")],
        [InlineKeyboardButton(text="🏋️ Фитнес", callback_data="n_fitness"),
         InlineKeyboardButton(text="💼 Другое", callback_data="n_other")]
    ])

@dp.message(CommandStart())
async def cmd_start(message: Message):
    uid = message.from_user.id
    sessions[uid] = {"niche": None, "count": 0, "history": []}
    await message.answer("👋 Привет! Я покажу как AI-ассистент может работать в вашем бизнесе.\n\n🎯 Выберите нишу:", reply_markup=get_keyboard())

@dp.callback_query(F.data.startswith("n_"))
async def on_niche(cb: CallbackQuery):
    uid = cb.from_user.id
    niche = cb.data[2:]
    sessions[uid] = {"niche": niche, "count": 0, "history": []}
    name = NICHE_NAMES.get(niche, niche)
    await cb.message.edit_text(f"✅ Отлично! Теперь я — AI-ассистент: {name}\n\n💬 Напишите мне как обычный клиент!")
    await cb.answer()

@dp.message(F.text)
async def on_text(message: Message):
    uid = message.from_user.id
    s = sessions.get(uid)
    if not s or not s.get("niche"):
        await message.answer("Пожалуйста, выберите нишу командой /start", reply_markup=get_keyboard())
        return
    
    prompt = PROMPTS.get(s["niche"], PROMPTS["other"])
    s["history"].append({"role": "user", "parts": [message.text]})
    
    try:
        chat = model.start_chat(history=s["history"][:-1])
        resp = chat.send_message(f"[System: {prompt}]\n\nКлиент: {message.text}")
        answer = resp.text
        s["history"].append({"role": "model", "parts": [answer]})
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        answer = "Извините, произошла ошибка. Попробуйте ещё раз!"
    
    s["count"] += 1
    if s["count"] >= 5:
        answer += CTA
    
    await message.answer(answer)

async def main():
    logger.info("🚀 AI Centers Demo Bot started!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
