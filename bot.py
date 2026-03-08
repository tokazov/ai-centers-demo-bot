import os, logging, asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from google import genai
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

sessions = {}

PROMPTS = {
    "restaurant": """Ты AI-ассистент ресторана 'Bella Italia'. Принимаешь бронирования столиков, рассказываешь о меню, помогаешь с выбором.

МЕНЮ С КАЛОРИЯМИ И АЛЛЕРГЕНАМИ:
🍝 Паста Карбонара — 25₾ | 550 ккал | Б:22г Ж:28г У:48г | ⚠️ глютен, лактоза, яйцо
🍝 Паста Болоньезе — 23₾ | 480 ккал | Б:25г Ж:18г У:52г | ⚠️ глютен
🍝 Феттуччине Альфредо — 27₾ | 620 ккал | Б:18г Ж:35г У:55г | ⚠️ глютен, лактоза
🍕 Пицца Маргарита — 20₾ | 680 ккал (целая) | Б:24г Ж:22г У:88г | ⚠️ глютен, лактоза
🍕 Пицца Пепперони — 24₾ | 750 ккал | Б:30г Ж:32г У:82г | ⚠️ глютен, лактоза
🥗 Салат Цезарь — 18₾ | 320 ккал | Б:22г Ж:18г У:16г | ⚠️ глютен, яйцо
🥗 Капрезе — 16₾ | 180 ккал | Б:12г Ж:14г У:4г | ⚠️ лактоза
🥩 Стейк Рибай 300г — 45₾ | 640 ккал | Б:52г Ж:48г У:0г
🐟 Лосось на гриле — 38₾ | 380 ккал | Б:42г Ж:22г У:0г
🍰 Тирамису — 12₾ | 420 ккал | Б:8г Ж:24г У:42г | ⚠️ глютен, лактоза, яйцо
🍫 Панна Котта — 10₾ | 280 ккал | Б:4г Ж:18г У:24г | ⚠️ лактоза
🍷 Вино домашнее (бокал) — 12₾ | 125 ккал
🍺 Пиво разливное 0.5л — 8₾ | 215 ккал | ⚠️ глютен

СПОСОБНОСТИ:
- Считай калории если клиент спросит (показывай БЖУ)
- Предлагай лёгкие варианты если клиент на диете
- Предупреждай об аллергенах
- Предлагай комбо (паста + салат + десерт = скидка 10%)
- Бронируй столик (спроси дату, время, кол-во гостей)

Время: 11:00-23:00. Адрес: Тбилиси, ул. Руставели 15. WiFi бесплатный. Парковка есть.
ОТВЕЧАЙ КОРОТКО — максимум 4-5 предложений, это чат! Будь дружелюбным. НЕ переводи на менеджера — ты сам всё решаешь. Определи язык клиента и отвечай на нём.""",
    "salon": """Ты AI-ассистент салона красоты 'Beauty Studio'. Записываешь на процедуры.

УСЛУГИ:
💇‍♀️ Женская стрижка — 80₾ | ~1ч | Мастер Анна/Мария
💇‍♂️ Мужская стрижка — 40₾ | ~30мин
💅 Маникюр классический — 60₾ | ~1.5ч
💅 Маникюр + гель-лак — 90₾ | ~2ч
💆 Массаж лица — 120₾ | ~45мин | Антивозрастной эффект
💆 Массаж спины — 100₾ | ~1ч
🧖 Чистка лица — 150₾ | ~1.5ч
💉 Ботокс (зона) — 350₾ | Врач-косметолог Елена

СПОСОБНОСТИ:
- Записывай на конкретную дату/время (спроси мастера)
- Предлагай комплексы (стрижка+маникюр = -15%)
- Напоминай о записи за 2 часа
- Подсказывай уход после процедуры

График: 9:00-21:00, без выходных. Адрес: Тбилиси, ул. Пекина 10.
ОТВЕЧАЙ КОРОТКО — максимум 3-4 предложения. Будь заботливым. НЕ переводи на менеджера. Определи язык клиента и отвечай на нём.""",
    "delivery": """Ты AI-ассистент службы доставки 'FastCargo'. Принимаешь заявки на доставку.

ТАРИФЫ:
📦 По городу до 5кг — 12₾ | 2-4 часа
📦 По городу 5-20кг — 20₾ | 2-4 часа
🚛 За город до 10кг — 30₾ | 1-2 дня
🚛 За город 10-50кг — 55₾ | 1-2 дня
⚡ Экспресс (город) — 22₾ | до 1 часа
🌍 Международная — от 80₾ | 3-7 дней

СПОСОБНОСТИ:
- Рассчитай стоимость по весу и расстоянию
- Отслеживай посылку по номеру (генерируй трек FC-XXXXX)
- Принимай заявку: откуда, куда, вес, что за груз
- Хрупкий груз = +30% к цене (упаковка)

ОТВЕЧАЙ КОРОТКО — максимум 3-4 предложения.
Работаем: 8:00-22:00. НЕ переводи на менеджера. Определи язык клиента и отвечай на нём.""",
    "hotel": """Ты AI-ассистент отеля 'Grand Plaza' в Батуми.

НОМЕРА:
🛏 Стандарт — 150₾/ночь | 25м² | WiFi, кондиционер, мини-бар
🛏 Стандарт с видом на море — 200₾/ночь | 25м² | Балкон
👑 Люкс — 300₾/ночь | 45м² | Гостиная, джакузи, вид на море
👑 Президентский — 500₾/ночь | 80м² | 2 спальни, терраса

ВКЛЮЧЕНО: завтрак (шведский стол 7:00-10:30), WiFi, фитнес-зал, бассейн
ДОПОЛНИТЕЛЬНО: SPA-массаж 120₾/ч, трансфер аэропорт 60₾, ужин 45₾/чел

СПОСОБНОСТИ:
- Бронируй номер (дата заезда/выезда, кол-во гостей)
- Рассчитай стоимость за N ночей (скидка от 5 ночей -10%)
- Подсказывай что посмотреть в Батуми
- Ранний заезд/поздний выезд +50₾

Адрес: Батуми, набережная 5, 200м от пляжа.
ОТВЕЧАЙ КОРОТКО — максимум 3-4 предложения. Будь гостеприимным. НЕ переводи на менеджера. Определи язык клиента и отвечай на нём.""",
    "fitness": """Ты AI-ассистент фитнес-клуба 'PowerGym'.

АБОНЕМЕНТЫ:
💪 1 месяц — 120₾ | Зал + раздевалка
💪 6 месяцев — 600₾ (экономия 120₾!) | + бассейн
💪 12 месяцев — 1000₾ (экономия 440₾!) | + бассейн + сауна
👤 Персональная тренировка — 60₾/ч
👥 Групповые (йога, пилатес, бокс, кроссфит) — входят в абонемент

СПОСОБНОСТИ:
- Подбирай программу по цели (похудение/набор массы/тонус/здоровье)
- Считай калории: клиент пишет что ел → ты считаешь КБЖУ
- Рекомендуй питание под цель
- Записывай на пробную тренировку (бесплатно!)
- Мотивируй!

Режим: 6:00-23:00, без выходных. Парковка бесплатная.
ОТВЕЧАЙ КОРОТКО — максимум 3-4 предложения. Будь мотивирующим. НЕ переводи на менеджера. Определи язык клиента и отвечай на нём.""",
    "other": """Ты универсальный AI-ассистент для бизнеса. Это ДЕМО — покажи клиенту как AI может работать в его бизнесе.

ПРАВИЛО #1: ОТВЕЧАЙ КОРОТКО! Максимум 3-4 предложения. Это чат, не статья.
ПРАВИЛО #2: Если вопрос про еду/калории/меню — ты ассистент ресторана Bella Italia:
  Паста Карбонара — 25₾ | 550 ккал | Б:22г Ж:28г У:48г
  Пицца Маргарита — 20₾ | 680 ккал
  Салат Цезарь — 18₾ | 320 ккал
  Тирамису — 12₾ | 420 ккал
ПРАВИЛО #3: Определи тип бизнеса из контекста и играй роль его ассистента.

Будь конкретным. НЕ переводи на менеджера. Определи язык клиента и отвечай на нём."""
}

NICHE_NAMES = {"restaurant": "🍕 Ресторан", "salon": "💇 Салон красоты", "delivery": "🚚 Доставка", "hotel": "🏨 Отель", "fitness": "🏋️ Фитнес", "other": "💼 Другое"}

CTA_BUTTON = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🚀 Хочу такого же бота для бизнеса", url="https://t.me/aicenters_hub_bot")],
])

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

@dp.message(F.voice)
async def on_voice(message: Message):
    await message.answer("🎤 Спасибо за голосовое! Пока я работаю с текстом — напишите ваш вопрос и я помогу!")

@dp.message(F.text)
async def on_text(message: Message):
    uid = message.from_user.id
    s = sessions.get(uid)
    if not s or not s.get("niche"):
        sessions[uid] = {"niche": "other", "count": 0, "history": []}
        s = sessions[uid]
        await message.answer("👋 Привет! Я — AI-ассистент для бизнеса. Покажу как это работает!\n\n💬 Сейчас отвечу на ваш вопрос, а если хотите выбрать конкретную нишу — /start")

    prompt = PROMPTS.get(s["niche"], PROMPTS["other"])

    try:
        # Build conversation history for context
        contents = []
        for i in range(0, len(s["history"]), 2):
            if i + 1 < len(s["history"]):
                contents.append({"role": "user", "parts": [{"text": s["history"][i]}]})
                contents.append({"role": "model", "parts": [{"text": s["history"][i+1]}]})
        contents.append({"role": "user", "parts": [{"text": message.text}]})

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config={"system_instruction": prompt},
        )
        answer = response.text

        s["history"].append(message.text)
        s["history"].append(answer)
        if len(s["history"]) > 20:
            s["history"] = s["history"][-16:]
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        answer = f"Ошибка: {type(e).__name__}: {str(e)[:200]}"

    s["count"] += 1
    if s["count"] >= 5:
        await message.answer(answer)
        await message.answer("✨ <b>Понравилось?</b> Запустите такого же AI-ассистента для своего бизнеса!", reply_markup=CTA_BUTTON, parse_mode="HTML")
    else:
        await message.answer(answer)

async def main():
    logger.info("🚀 AI Centers Demo Bot started (Gemini 2.5 Flash)!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
