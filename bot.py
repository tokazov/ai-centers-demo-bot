import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import google.generativeai as genai
from collections import defaultdict
import asyncio

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "8672975647:AAHpWG5xTxLRv0IKKy6tvl_VlAn_FfL99vM")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDRJLp8JGpKid1pTJBRVgeumPdObveAXwY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Bot initialization
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# States
class DemoState(StatesGroup):
    choosing_niche = State()
    chatting = State()

# User sessions
user_sessions = defaultdict(lambda: {"niche": None, "message_count": 0, "history": []})

# Niche prompts
NICHE_PROMPTS = {
    "restaurant": {
        "ru": "Ты AI-ассистент ресторана 'Bella Italia'. Принимаешь бронирования столиков, рассказываешь о меню (паста, пицца, десерты), помогаешь с заказами. Будь дружелюбным и профессиональным. Меню: Паста Карбонара - 890₽, Пицца Маргарита - 750₽, Тирамису - 450₽. Рабочее время: 11:00-23:00. Отвечай на русском языке.",
        "en": "You are an AI assistant for 'Bella Italia' restaurant. Take table reservations, tell about menu (pasta, pizza, desserts), help with orders. Be friendly and professional. Menu: Carbonara Pasta - $15, Margherita Pizza - $12, Tiramisu - $8. Working hours: 11:00-23:00. Respond in English.",
        "ka": "შენ ხარ AI ასისტენტი რესტორანისთვის 'Bella Italia'. მიიღე ჯავშნები, ესაუბრე მენიუზე (პასტა, პიცა, დესერტები), დაეხმარე შეკვეთებში. იყავი მეგობრული და პროფესიონალი. მენიუ: კარბონარა პასტა - 25₾, მარგარიტა პიცა - 20₾, ტირამისუ - 12₾. სამუშაო საათები: 11:00-23:00. პასუხობდი ქართულად.",
        "tr": "Bella Italia restoranının AI asistanısınız. Masa rezervasyonları alın, menüden (makarna, pizza, tatlılar) bahsedin, siparişlerde yardımcı olun. Samimi ve profesyonel olun. Menü: Carbonara Makarna - 450₺, Margherita Pizza - 380₺, Tiramisu - 200₺. Çalışma saatleri: 11:00-23:00. Türkçe yanıt verin."
    },
    "salon": {
        "ru": "Ты AI-ассистент салона красоты 'Beauty Studio'. Записываешь на процедуры (стрижка, маникюр, массаж), рассказываешь об услугах и ценах. Услуги: Женская стрижка - 2500₽, Маникюр - 1800₽, Массаж лица - 3500₽. График: 9:00-21:00. Будь дружелюбным и заботливым. Отвечай на русском языке.",
        "en": "You are an AI assistant for 'Beauty Studio' salon. Book appointments (haircut, manicure, massage), tell about services and prices. Services: Women's haircut - $40, Manicure - $30, Face massage - $55. Schedule: 9:00-21:00. Be friendly and caring. Respond in English.",
        "ka": "შენ ხარ AI ასისტენტი სალონისთვის 'Beauty Studio'. ჩაწერე პროცედურებზე (თმის შეჭრა, მანიკური, მასაჟი), ესაუბრე სერვისებზე და ფასებზე. სერვისები: ქალის თმის შეჭრა - 80₾, მანიკური - 60₾, სახის მასაჟი - 120₾. გრაფიკი: 9:00-21:00. იყავი მეგობრული და მზრუნველი. პასუხობდი ქართულად.",
        "tr": "Beauty Studio güzellik salonunun AI asistanısınız. Randevu alın (saç kesimi, manikür, masaj), hizmetler ve fiyatlar hakkında bilgi verin. Hizmetler: Kadın saç kesimi - 800₺, Manikür - 600₺, Yüz masajı - 1200₺. Program: 9:00-21:00. Samimi ve ilgili olun. Türkçe yanıt verin."
    },
    "delivery": {
        "ru": "Ты AI-ассистент службы доставки 'FastCargo'. Принимаешь заявки на доставку, рассказываешь о тарифах и сроках. Тарифы: По городу (до 5кг) - 350₽, За город (до 10кг) - 890₽, Экспресс - 650₽. Доставка 1-3 дня. Будь оперативным и чётким. Отвечай на русском языке.",
        "en": "You are an AI assistant for 'FastCargo' delivery service. Take delivery orders, tell about rates and timeframes. Rates: City (up to 5kg) - $6, Suburbs (up to 10kg) - $15, Express - $11. Delivery 1-3 days. Be efficient and clear. Respond in English.",
        "ka": "შენ ხარ AI ასისტენტი მიწოდების სერვისისთვის 'FastCargo'. მიიღე მიწოდების შეკვეთები, ესაუბრე ტარიფებზე და ვადებზე. ტარიფები: ქალაქში (5კგ-მდე) - 12₾, გარეუბანში (10კგ-მდე) - 30₾, ექსპრესი - 22₾. მიწოდება 1-3 დღე. იყავი ოპერატიული და ზუსტი. პასუხობდი ქართულად.",
        "tr": "FastCargo teslimat hizmetinin AI asistanısınız. Teslimat siparişleri alın, tarifeler ve süreler hakkında bilgi verin. Tarifeler: Şehir içi (5kg'a kadar) - 200₺, Şehir dışı (10kg'a kadar) - 450₺, Ekspres - 350₺. Teslimat 1-3 gün. Hızlı ve net olun. Türkçe yanıt verin."
    },
    "hotel": {
        "ru": "Ты AI-ассистент отеля 'Grand Plaza'. Принимаешь бронирования номеров, рассказываешь об услугах (spa, ресторан, конференц-зал). Номера: Стандарт - 4500₽/ночь, Люкс - 8900₽/ночь. Услуги: SPA, фитнес, завтрак включён. Будь гостеприимным и внимательным. Отвечай на русском языке.",
        "en": "You are an AI assistant for 'Grand Plaza' hotel. Take room reservations, tell about services (spa, restaurant, conference hall). Rooms: Standard - $75/night, Suite - $145/night. Services: SPA, fitness, breakfast included. Be hospitable and attentive. Respond in English.",
        "ka": "შენ ხარ AI ასისტენტი სასტუმროსთვის 'Grand Plaza'. მიიღე ნომრების ჯავშნები, ესაუბრე სერვისებზე (spa, რესტორანი, საკონფერენციო დარბაზი). ნომრები: სტანდარტი - 150₾/ღამე, ლუქსი - 300₾/ღამე. სერვისები: SPA, ფიტნესი, საუზმე ჩართულია. იყავი სტუმართმოყვარე და ყურადღებიანი. პასუხობდი ქართულად.",
        "tr": "Grand Plaza otelinin AI asistanısınız. Oda rezervasyonları alın, hizmetlerden (spa, restoran, konferans salonu) bahsedin. Odalar: Standart - 2500₺/gece, Suit - 4800₺/gece. Hizmetler: SPA, fitness, kahvaltı dahil. Misafirperver ve özenli olun. Türkçe yanıt verin."
    },
    "fitness": {
        "ru": "Ты AI-ассистент фитнес-клуба 'PowerGym'. Записываешь на тренировки, рассказываешь об абонементах и услугах. Абонементы: 1 месяц - 3500₽, 6 месяцев - 18000₽, год - 30000₽. Услуги: тренажёрный зал, бассейн, групповые занятия, персональный тренер. Режим: 6:00-23:00. Будь мотивирующим и энергичным. Отвечай на русском языке.",
        "en": "You are an AI assistant for 'PowerGym' fitness club. Book training sessions, tell about memberships and services. Memberships: 1 month - $55, 6 months - $290, year - $480. Services: gym, pool, group classes, personal trainer. Hours: 6:00-23:00. Be motivating and energetic. Respond in English.",
        "ka": "შენ ხარ AI ასისტენტი ფიტნეს კლუბისთვის 'PowerGym'. ჩაწერე ვარჯიშებზე, ესაუბრე აბონემენტებზე და სერვისებზე. აბონემენტები: 1 თვე - 120₾, 6 თვე - 600₾, წელი - 1000₾. სერვისები: სავარჯიშო დარბაზი, აუზი, ჯგუფური მეცადინეობები, პირადი მწვრთნელი. რეჟიმი: 6:00-23:00. იყავი მოტივირებული და ენერგიული. პასუხობდი ქართულად.",
        "tr": "PowerGym fitness kulübünün AI asistanısınız. Antrenman rezervasyonları alın, üyelikler ve hizmetler hakkında bilgi verin. Üyelikler: 1 ay - 1800₺, 6 ay - 9500₺, yıl - 16000₺. Hizmetler: spor salonu, havuz, grup dersleri, kişisel antrenör. Saatler: 6:00-23:00. Motive edici ve enerjik olun. Türkçe yanıt verin."
    },
    "other": {
        "ru": "Ты универсальный AI-ассистент для бизнеса. Помогаешь клиентам с информацией, принимаешь заявки, консультируешь. Будь вежливым, профессиональным и полезным. Отвечай на русском языке.",
        "en": "You are a universal AI business assistant. Help clients with information, take requests, provide consultations. Be polite, professional and helpful. Respond in English.",
        "ka": "შენ ხარ უნივერსალური AI ასისტენტი ბიზნესისთვის. დაეხმარე კლიენტებს ინფორმაციით, მიიღე განცხადებები, მიეცი კონსულტაციები. იყავი თავაზიანი, პროფესიონალი და სასარგებლო. პასუხობდი ქართულად.",
        "tr": "Evrensel bir AI iş asistanısınız. Müşterilere bilgi verin, talep alın, danışmanlık yapın. Kibar, profesyonel ve yardımcı olun. Türkçe yanıt verin."
    }
}

# Welcome messages
WELCOME_MESSAGES = {
    "ru": "👋 Привет! Я покажу как AI-ассистент может работать в вашем бизнесе.\n\n🎯 Выберите нишу:",
    "en": "👋 Hello! I'll show you how an AI assistant can work in your business.\n\n🎯 Choose your niche:",
    "ka": "👋 გამარჯობა! მე გიჩვენებ როგორ შეუძლია AI ასისტენტს იმუშაოს შენს ბიზნესში.\n\n🎯 აირჩიე ნიშა:",
    "tr": "👋 Merhaba! Size bir AI asistanın işinizde nasıl çalışabileceğini göstereceğim.\n\n🎯 Bir niş seçin:"
}

# Niche buttons
NICHE_BUTTONS = {
    "ru": {
        "restaurant": "🍕 Ресторан",
        "salon": "💇 Салон красоты",
        "delivery": "🚚 Доставка",
        "hotel": "🏨 Отель",
        "fitness": "🏋️ Фитнес",
        "other": "💼 Другое"
    },
    "en": {
        "restaurant": "🍕 Restaurant",
        "salon": "💇 Beauty Salon",
        "delivery": "🚚 Delivery",
        "hotel": "🏨 Hotel",
        "fitness": "🏋️ Fitness",
        "other": "💼 Other"
    },
    "ka": {
        "restaurant": "🍕 რესტორანი",
        "salon": "💇 სალონი",
        "delivery": "🚚 მიწოდება",
        "hotel": "🏨 სასტუმრო",
        "fitness": "🏋️ ფიტნესი",
        "other": "💼 სხვა"
    },
    "tr": {
        "restaurant": "🍕 Restoran",
        "salon": "💇 Güzellik Salonu",
        "delivery": "🚚 Teslimat",
        "hotel": "🏨 Otel",
        "fitness": "🏋️ Fitness",
        "other": "💼 Diğer"
    }
}

# CTA messages
CTA_MESSAGES = {
    "ru": "\n\n✨ Понравилось?\n\n🚀 Мы можем настроить такого же AI-ассистента для вашего бизнеса за 24 часа!\n\n👉 Узнать подробнее: @ai_centers_hub_bot",
    "en": "\n\n✨ Like it?\n\n🚀 We can set up the same AI assistant for your business within 24 hours!\n\n👉 Learn more: @ai_centers_hub_bot",
    "ka": "\n\n✨ მოგეწონა?\n\n🚀 ჩვენ შეგვიძლია დავაყენოთ იგივე AI ასისტენტი შენი ბიზნესისთვის 24 საათში!\n\n👉 გაიგე მეტი: @ai_centers_hub_bot",
    "tr": "\n\n✨ Beğendiniz mi?\n\n🚀 Aynı AI asistanı işiniz için 24 saat içinde kurabiliriz!\n\n👉 Daha fazla bilgi: @ai_centers_hub_bot"
}

def detect_language(text: str) -> str:
    """Detect user language"""
    text_lower = text.lower()
    
    # Georgian detection
    if any(char in text for char in 'აბგდევზთიკლმნოპჟრსტუფქღყშჩცძწჭხჯჰ'):
        return "ka"
    
    # Turkish detection
    if any(word in text_lower for word in ['merhaba', 'nasıl', 'teşekkür', 'evet', 'hayır']):
        return "tr"
    
    # English detection
    if any(word in text_lower for word in ['hello', 'hi', 'thank', 'yes', 'no', 'please']):
        return "en"
    
    # Default to Russian
    return "ru"

def get_niche_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Create niche selection keyboard"""
    buttons = NICHE_BUTTONS.get(lang, NICHE_BUTTONS["ru"])
    
    keyboard = [
        [
            InlineKeyboardButton(text=buttons["restaurant"], callback_data="niche:restaurant"),
            InlineKeyboardButton(text=buttons["salon"], callback_data="niche:salon")
        ],
        [
            InlineKeyboardButton(text=buttons["delivery"], callback_data="niche:delivery"),
            InlineKeyboardButton(text=buttons["hotel"], callback_data="niche:hotel")
        ],
        [
            InlineKeyboardButton(text=buttons["fitness"], callback_data="niche:fitness"),
            InlineKeyboardButton(text=buttons["other"], callback_data="niche:other")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def get_ai_response(prompt: str, user_message: str, history: list, lang: str = "ru") -> str:
    """Get response from Gemini API"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Build conversation history
        conversation = []
        
        for msg in history[-10:]:  # Keep last 10 messages for context
            conversation.append(msg)
        
        # Add system prompt as first user message
        full_prompt = f"{prompt}\n\nUser message: {user_message}"
        
        # Generate response
        if conversation:
            chat = model.start_chat(history=conversation)
            response = chat.send_message(full_prompt)
        else:
            response = model.generate_content(full_prompt)
        
        return response.text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        error_messages = {
            "ru": "Извините, произошла ошибка. Попробуйте ещё раз.",
            "en": "Sorry, an error occurred. Please try again.",
            "ka": "უკაცრავად, მოხდა შეცდომა. სცადეთ ხელახლა.",
            "tr": "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin."
        }
        return error_messages.get(lang, error_messages["ru"])

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command"""
    user_id = message.from_user.id
    
    # Detect language from user profile or message
    lang = "ru"
    if message.from_user.language_code:
        lang_code = message.from_user.language_code.lower()
        if lang_code in ["en", "ka", "tr"]:
            lang = lang_code
        elif lang_code.startswith("ru"):
            lang = "ru"
    
    # Reset session
    user_sessions[user_id] = {"niche": None, "message_count": 0, "history": [], "lang": lang}
    
    welcome_text = WELCOME_MESSAGES.get(lang, WELCOME_MESSAGES["ru"])
    
    await message.answer(
        welcome_text,
        reply_markup=get_niche_keyboard(lang)
    )
    
    await state.set_state(DemoState.choosing_niche)

@dp.callback_query(F.data.startswith("niche:"))
async def select_niche(callback: CallbackQuery, state: FSMContext):
    """Handle niche selection"""
    user_id = callback.from_user.id
    niche = callback.data.split(":")[1]
    
    # Store niche
    user_sessions[user_id]["niche"] = niche
    user_sessions[user_id]["message_count"] = 0
    user_sessions[user_id]["history"] = []
    
    lang = user_sessions[user_id].get("lang", "ru")
    
    # Confirmation messages
    confirmations = {
        "ru": f"✅ Отлично! Теперь я работаю как AI-ассистент для ниши: {NICHE_BUTTONS['ru'].get(niche, 'Другое')}\n\n💬 Напишите мне что-нибудь, и я покажу как помогаю клиентам!",
        "en": f"✅ Great! Now I'm working as an AI assistant for: {NICHE_BUTTONS['en'].get(niche, 'Other')}\n\n💬 Write me something and I'll show you how I help clients!",
        "ka": f"✅ შესანიშნავია! ახლა მე ვმუშაობ როგორც AI ასისტენტი: {NICHE_BUTTONS['ka'].get(niche, 'სხვა')}\n\n💬 დამწერე რამე და გიჩვენებ როგორ ვეხმარები კლიენტებს!",
        "tr": f"✅ Harika! Şimdi şu niş için AI asistanı olarak çalışıyorum: {NICHE_BUTTONS['tr'].get(niche, 'Diğer')}\n\n💬 Bana bir şeyler yazın ve müşterilere nasıl yardımcı olduğumu göstereyim!"
    }
    
    await callback.message.edit_text(confirmations.get(lang, confirmations["ru"]))
    await state.set_state(DemoState.chatting)
    await callback.answer()

@dp.message(F.text.startswith("/reset"))
async def cmd_reset(message: Message, state: FSMContext):
    """Reset and go back to niche selection"""
    user_id = message.from_user.id
    lang = user_sessions[user_id].get("lang", "ru")
    
    # Reset session but keep language
    user_sessions[user_id] = {"niche": None, "message_count": 0, "history": [], "lang": lang}
    
    reset_messages = {
        "ru": "🔄 Хорошо, давайте начнём заново!\n\n🎯 Выберите нишу:",
        "en": "🔄 Okay, let's start over!\n\n🎯 Choose your niche:",
        "ka": "🔄 კარგი, დავიწყოთ თავიდან!\n\n🎯 აირჩიე ნიშა:",
        "tr": "🔄 Tamam, baştan başlayalım!\n\n🎯 Bir niş seçin:"
    }
    
    await message.answer(
        reset_messages.get(lang, reset_messages["ru"]),
        reply_markup=get_niche_keyboard(lang)
    )
    
    await state.set_state(DemoState.choosing_niche)

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_message(message: Message, state: FSMContext):
    """Handle user messages in chat mode"""
    user_id = message.from_user.id
    session = user_sessions[user_id]
    
    niche = session.get("niche")
    lang = session.get("lang", "ru")
    
    if not niche:
        await message.answer("Пожалуйста, выберите нишу командой /start")
        return
    
    # Get niche prompt
    system_prompt = NICHE_PROMPTS.get(niche, {}).get(lang, NICHE_PROMPTS[niche]["ru"])
    
    # Get AI response
    user_message = message.text
    response = await get_ai_response(system_prompt, user_message, session["history"], lang)
    
    # Update history
    session["history"].append({"role": "user", "parts": [user_message]})
    session["history"].append({"role": "model", "parts": [response]})
    
    # Increment message count
    session["message_count"] += 1
    
    # Show CTA after 5-7 messages
    if session["message_count"] >= 5:
        response += CTA_MESSAGES.get(lang, CTA_MESSAGES["ru"])
    
    await message.answer(response)

async def main():
    """Main function"""
    logger.info("🚀 AI Centers Demo Bot started!")
    
    # Delete webhook to use polling
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
