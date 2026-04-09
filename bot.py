import logging
import os
from dataclasses import dataclass
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, status
import uvicorn

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

ROLE_CLIENT = "client"
ROLE_ADMIN = "admin"
ROLE_BUTTON_TO_CODE = {
    "🙋‍♀️ Client / Klient": ROLE_CLIENT,
    "👩‍💼 Admin": ROLE_ADMIN,
}

DEMO_BOOKINGS: list[dict] = []
DEMO_QUESTIONS: list[dict] = []


@dataclass(frozen=True)
class Service:
    key: str
    names: dict[str, str]
    descriptions: dict[str, str]


SERVICES = [
    Service(
        key="facial",
        names={"uz": "Yuz terisi davolash", "ru": "Уход за лицом", "en": "Facial Treatment"},
        descriptions={
            "uz": "Terini tozalash, namlash va tiklash muolajasi.",
            "ru": "Очищение, увлажнение и восстановление кожи.",
            "en": "Skin cleansing, hydration, and recovery treatment.",
        },
    ),
    Service(
        key="laser",
        names={"uz": "Lazer epilatsiya", "ru": "Лазерная эпиляция", "en": "Laser Epilation"},
        descriptions={
            "uz": "Nozik va samarali lazer epilatsiya xizmati.",
            "ru": "Деликатная и эффективная лазерная эпиляция.",
            "en": "Gentle and effective laser epilation service.",
        },
    ),
    Service(
        key="consultation",
        names={
            "uz": "Kosmetologik maslahat",
            "ru": "Консультация косметолога",
            "en": "Cosmetology Consultation",
        },
        descriptions={
            "uz": "Mutaxassisdan teri holati bo'yicha shaxsiy tavsiyalar.",
            "ru": "Персональные рекомендации по уходу от специалиста.",
            "en": "Personal skincare recommendations from a specialist.",
        },
    ),
]

TIME_SLOTS = [
    {"key": "today_14", "time": "14:00", "delta_days": 0},
    {"key": "today_16", "time": "16:00", "delta_days": 0},
    {"key": "tomorrow_11", "time": "11:00", "delta_days": 1},
]

I18N = {
    "uz": {
        "welcome": "Xush kelibsiz 💖 Demo salon botiga hush kelibsiz.",
        "choose_interface": "Interfeysni tanlang:",
        "choose_language": "Tilni tanlang:",
        "menu_services": "Xizmatlar",
        "menu_book": "Yozilish",
        "menu_ask": "Savol berish",
        "menu_switch_interface": "Interfeysni almashtirish",
        "menu_text": "Asosiy menyu ✨",
        "client_only": "Bu bo'lim faqat klient interfeysi uchun.",
        "services_title": "Xizmatlarimiz 💆‍♀️",
        "book_button": "Yozilish",
        "book_step_service": "Qaysi xizmatni tanlaysiz?",
        "book_step_time": "Qulay vaqtni tanlang:",
        "book_step_name": "Ismingizni kiriting:",
        "book_step_phone": "Telefon raqamingizni yuboring:",
        "send_contact": "📱 Kontakt yuborish",
        "confirm": "Sizning yozuvingiz tasdiqlandi 💖",
        "reminder": "Eslatma: {service} vaqti yaqinlashmoqda 💖",
        "ask_prompt": "Savolingizni yuboring 💬",
        "ask_reply": "Sizning savolingiz qabul qilindi, administrator javob beradi 💬",
        "admin_menu_text": "Admin menyu 👩‍💼",
        "admin_menu_dashboard": "Dashboard",
        "admin_menu_bookings": "Yozuvlar",
        "admin_menu_questions": "Savollar",
        "admin_dashboard": "Demo statistikasi\n• Jami yozuvlar: {bookings}\n• Jami savollar: {questions}",
        "admin_empty_bookings": "Hozircha yozuvlar yo'q.",
        "admin_empty_questions": "Hozircha savollar yo'q.",
        "admin_bookings_title": "Oxirgi yozuvlar:",
        "admin_questions_title": "Oxirgi savollar:",
        "today": "Bugun",
        "tomorrow": "Ertaga",
        "lang_name": "🇺🇿 O'zbekcha",
    },
    "ru": {
        "welcome": "Добро пожаловать 💖 Это демо-бот салона.",
        "choose_interface": "Выберите интерфейс:",
        "choose_language": "Выберите язык:",
        "menu_services": "Услуги",
        "menu_book": "Записаться",
        "menu_ask": "Задать вопрос",
        "menu_switch_interface": "Сменить интерфейс",
        "menu_text": "Главное меню ✨",
        "client_only": "Этот раздел доступен только клиенту.",
        "services_title": "Наши услуги 💆‍♀️",
        "book_button": "Записаться",
        "book_step_service": "Выберите услугу:",
        "book_step_time": "Выберите удобное время:",
        "book_step_name": "Введите ваше имя:",
        "book_step_phone": "Введите номер телефона:",
        "send_contact": "📱 Отправить контакт",
        "confirm": "Ваша запись подтверждена 💖",
        "reminder": "Напоминание: {service} скоро начинается 💖",
        "ask_prompt": "Отправьте ваш вопрос 💬",
        "ask_reply": "Ваш вопрос принят, администратор ответит 💬",
        "admin_menu_text": "Меню админа 👩‍💼",
        "admin_menu_dashboard": "Дашборд",
        "admin_menu_bookings": "Записи",
        "admin_menu_questions": "Вопросы",
        "admin_dashboard": "Демо-статистика\n• Всего записей: {bookings}\n• Всего вопросов: {questions}",
        "admin_empty_bookings": "Пока нет записей.",
        "admin_empty_questions": "Пока нет вопросов.",
        "admin_bookings_title": "Последние записи:",
        "admin_questions_title": "Последние вопросы:",
        "today": "Сегодня",
        "tomorrow": "Завтра",
        "lang_name": "🇷🇺 Русский",
    },
    "en": {
        "welcome": "Welcome 💖 This is a beauty salon demo bot.",
        "choose_interface": "Choose interface:",
        "choose_language": "Choose your language:",
        "menu_services": "Services",
        "menu_book": "Book Appointment",
        "menu_ask": "Ask a Question",
        "menu_switch_interface": "Switch Interface",
        "menu_text": "Main menu ✨",
        "client_only": "This section is for client interface only.",
        "services_title": "Our Services 💆‍♀️",
        "book_button": "Book Appointment",
        "book_step_service": "Choose a service:",
        "book_step_time": "Choose a time:",
        "book_step_name": "Enter your name:",
        "book_step_phone": "Enter your phone number:",
        "send_contact": "📱 Send Contact",
        "confirm": "Your appointment is confirmed 💖",
        "reminder": "Reminder: Your {service} appointment is coming up 💖",
        "ask_prompt": "Send your question 💬",
        "ask_reply": "Your question has been received, administrator will respond 💬",
        "admin_menu_text": "Admin menu 👩‍💼",
        "admin_menu_dashboard": "Dashboard",
        "admin_menu_bookings": "Bookings",
        "admin_menu_questions": "Questions",
        "admin_dashboard": "Demo stats\n• Total bookings: {bookings}\n• Total questions: {questions}",
        "admin_empty_bookings": "No bookings yet.",
        "admin_empty_questions": "No questions yet.",
        "admin_bookings_title": "Latest bookings:",
        "admin_questions_title": "Latest questions:",
        "today": "Today",
        "tomorrow": "Tomorrow",
        "lang_name": "🇬🇧 English",
    },
}

LANG_BUTTON_TO_CODE = {I18N[code]["lang_name"]: code for code in I18N}
SERVICE_BY_KEY = {service.key: service for service in SERVICES}


def t(lang: str, key: str) -> str:
    return I18N.get(lang, I18N["en"])[key]


def language_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[I18N["uz"]["lang_name"], I18N["ru"]["lang_name"], I18N["en"]["lang_name"]]],
        resize_keyboard=True,
    )


def role_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["🙋‍♀️ Client / Klient", "👩‍💼 Admin"]],
        resize_keyboard=True,
    )


def client_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [t(lang, "menu_services")],
            [t(lang, "menu_book")],
            [t(lang, "menu_ask")],
            [t(lang, "menu_switch_interface")],
        ],
        resize_keyboard=True,
    )


def admin_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [t(lang, "admin_menu_dashboard")],
            [t(lang, "admin_menu_bookings"), t(lang, "admin_menu_questions")],
            [t(lang, "menu_switch_interface")],
        ],
        resize_keyboard=True,
    )


def phone_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton(t(lang, "send_contact"), request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def service_picker(lang: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(service.names[lang], callback_data=f"pick_service:{service.key}")]
        for service in SERVICES
    ]
    return InlineKeyboardMarkup(rows)


def time_picker(lang: str) -> InlineKeyboardMarkup:
    rows = []
    for slot in TIME_SLOTS:
        day = t(lang, "today") if slot["delta_days"] == 0 else t(lang, "tomorrow")
        rows.append(
            [
                InlineKeyboardButton(
                    f"{day} {slot['time']}",
                    callback_data=f"pick_time:{slot['key']}",
                )
            ]
        )
    return InlineKeyboardMarkup(rows)


def find_slot(slot_key: str) -> dict:
    for slot in TIME_SLOTS:
        if slot["key"] == slot_key:
            return slot
    raise ValueError(f"Unknown slot: {slot_key}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.effective_message.reply_text(
        "\n".join([I18N["uz"]["welcome"], I18N["ru"]["welcome"], I18N["en"]["welcome"]])
        + "\n\n"
        + "\n".join([I18N["uz"]["choose_interface"], I18N["ru"]["choose_interface"], I18N["en"]["choose_interface"]]),
        reply_markup=role_keyboard(),
    )


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = context.user_data.get("lang", "en")
    role = context.user_data.get("role")
    if role == ROLE_ADMIN:
        await update.effective_message.reply_text(t(lang, "admin_menu_text"), reply_markup=admin_menu_keyboard(lang))
        return
    await update.effective_message.reply_text(t(lang, "menu_text"), reply_markup=client_menu_keyboard(lang))


async def show_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = context.user_data.get("lang", "en")
    await update.effective_message.reply_text(t(lang, "services_title"))
    for service in SERVICES:
        text = f"💆‍♀️ {service.names[lang]}\n✨ {service.descriptions[lang]}"
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(t(lang, "book_button"), callback_data=f"quick_book:{service.key}")]]
        )
        await update.effective_message.reply_text(text, reply_markup=keyboard)


async def show_admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = context.user_data.get("lang", "en")
    await update.effective_message.reply_text(
        t(lang, "admin_dashboard").format(bookings=len(DEMO_BOOKINGS), questions=len(DEMO_QUESTIONS)),
        reply_markup=admin_menu_keyboard(lang),
    )


async def show_admin_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = context.user_data.get("lang", "en")
    if not DEMO_BOOKINGS:
        await update.effective_message.reply_text(t(lang, "admin_empty_bookings"), reply_markup=admin_menu_keyboard(lang))
        return

    lines = [t(lang, "admin_bookings_title")]
    for item in DEMO_BOOKINGS[-10:]:
        lines.append(f"• {item['service']} | {item['time']} | {item['name']} | {item['phone']}")
    await update.effective_message.reply_text("\n".join(lines), reply_markup=admin_menu_keyboard(lang))


async def show_admin_questions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = context.user_data.get("lang", "en")
    if not DEMO_QUESTIONS:
        await update.effective_message.reply_text(t(lang, "admin_empty_questions"), reply_markup=admin_menu_keyboard(lang))
        return

    lines = [t(lang, "admin_questions_title")]
    for item in DEMO_QUESTIONS[-10:]:
        lines.append(f"• {item['name']}: {item['text']}")
    await update.effective_message.reply_text("\n".join(lines), reply_markup=admin_menu_keyboard(lang))


async def start_booking(update: Update, context: ContextTypes.DEFAULT_TYPE, service_key: str | None = None) -> None:
    lang = context.user_data.get("lang", "en")
    context.user_data["state"] = "booking_service"

    if service_key:
        context.user_data["booking_service"] = service_key
        context.user_data["state"] = "booking_time"
        await update.effective_message.reply_text(t(lang, "book_step_time"), reply_markup=time_picker(lang))
        return

    await update.effective_message.reply_text(t(lang, "book_step_service"), reply_markup=service_picker(lang))


async def schedule_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    job_data = context.job.data
    await context.bot.send_message(
        chat_id=job_data["chat_id"],
        text=t(job_data["lang"], "reminder").format(service=job_data["service_name"]),
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("lang", "en")
    if context.user_data.get("role") != ROLE_CLIENT:
        await query.message.reply_text(t(lang, "client_only"), reply_markup=admin_menu_keyboard(lang))
        return
    data = query.data or ""

    if data.startswith("quick_book:"):
        service_key = data.split(":", maxsplit=1)[1]
        context.user_data["booking_service"] = service_key
        context.user_data["state"] = "booking_time"
        await query.message.reply_text(t(lang, "book_step_time"), reply_markup=time_picker(lang))
        return

    if data.startswith("pick_service:"):
        service_key = data.split(":", maxsplit=1)[1]
        context.user_data["booking_service"] = service_key
        context.user_data["state"] = "booking_time"
        await query.message.reply_text(t(lang, "book_step_time"), reply_markup=time_picker(lang))
        return

    if data.startswith("pick_time:"):
        slot_key = data.split(":", maxsplit=1)[1]
        context.user_data["booking_time"] = slot_key
        context.user_data["state"] = "booking_name"
        await query.message.reply_text(t(lang, "book_step_name"), reply_markup=ReplyKeyboardRemove())


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    text = (message.text or "").strip()

    # Step 0: Interface selection
    if text in ROLE_BUTTON_TO_CODE:
        context.user_data["role"] = ROLE_BUTTON_TO_CODE[text]
        await message.reply_text(
            "\n".join([I18N["uz"]["choose_language"], I18N["ru"]["choose_language"], I18N["en"]["choose_language"]]),
            reply_markup=language_keyboard(),
        )
        return

    if "role" not in context.user_data:
        await message.reply_text(
            "\n".join([I18N["uz"]["choose_interface"], I18N["ru"]["choose_interface"], I18N["en"]["choose_interface"]]),
            reply_markup=role_keyboard(),
        )
        return

    # Step 1: Language selection
    if text in LANG_BUTTON_TO_CODE:
        lang = LANG_BUTTON_TO_CODE[text]
        context.user_data["lang"] = lang
        context.user_data["state"] = "idle"
        await show_menu(update, context)
        return

    lang = context.user_data.get("lang")
    if not lang:
        await message.reply_text(
            "Please choose language first / Сначала выберите язык / Avval tilni tanlang",
            reply_markup=language_keyboard(),
        )
        return

    role = context.user_data.get("role", ROLE_CLIENT)
    state = context.user_data.get("state", "idle")

    if text == t(lang, "menu_switch_interface"):
        context.user_data.clear()
        await message.reply_text(
            "\n".join([I18N["uz"]["choose_interface"], I18N["ru"]["choose_interface"], I18N["en"]["choose_interface"]]),
            reply_markup=role_keyboard(),
        )
        return

    if role == ROLE_ADMIN:
        if text == t(lang, "admin_menu_dashboard"):
            await show_admin_dashboard(update, context)
            return
        if text == t(lang, "admin_menu_bookings"):
            await show_admin_bookings(update, context)
            return
        if text == t(lang, "admin_menu_questions"):
            await show_admin_questions(update, context)
            return
        await show_menu(update, context)
        return

    if state == "booking_name":
        context.user_data["booking_name"] = text
        context.user_data["state"] = "booking_phone"
        await message.reply_text(t(lang, "book_step_phone"), reply_markup=phone_keyboard(lang))
        return

    if state == "booking_phone":
        phone = text
        await finish_booking(update, context, phone)
        return

    if state == "asking_question":
        context.user_data["state"] = "idle"
        DEMO_QUESTIONS.append(
            {
                "chat_id": update.effective_chat.id,
                "name": update.effective_user.full_name,
                "text": text,
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
        await message.reply_text(t(lang, "ask_reply"), reply_markup=client_menu_keyboard(lang))
        return

    if text == t(lang, "menu_services"):
        await show_services(update, context)
        return

    if text == t(lang, "menu_book"):
        await start_booking(update, context)
        return

    if text == t(lang, "menu_ask"):
        context.user_data["state"] = "asking_question"
        await message.reply_text(t(lang, "ask_prompt"), reply_markup=ReplyKeyboardRemove())
        return

    await show_menu(update, context)


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = context.user_data.get("lang", "en")
    if context.user_data.get("state") != "booking_phone":
        await update.effective_message.reply_text(t(lang, "menu_text"), reply_markup=client_menu_keyboard(lang))
        return

    contact = update.effective_message.contact
    phone = contact.phone_number if contact else ""
    await finish_booking(update, context, phone)


async def finish_booking(update: Update, context: ContextTypes.DEFAULT_TYPE, phone: str) -> None:
    lang = context.user_data.get("lang", "en")
    service_key = context.user_data.get("booking_service")
    if not service_key or service_key not in SERVICE_BY_KEY:
        context.user_data["state"] = "idle"
        await update.effective_message.reply_text(t(lang, "menu_text"), reply_markup=client_menu_keyboard(lang))
        return

    service = SERVICE_BY_KEY[service_key]
    service_name = service.names[lang]

    slot = find_slot(context.user_data.get("booking_time", "today_14"))
    reminder_delay_seconds = 90

    context.job_queue.run_once(
        schedule_reminder,
        when=reminder_delay_seconds,
        data={
            "chat_id": update.effective_chat.id,
            "lang": lang,
            "service_name": service_name,
        },
        name=f"reminder_{update.effective_user.id}_{datetime.now().timestamp()}",
    )

    context.user_data.update(
        {
            "state": "idle",
            "last_booking": {
                "service": service_name,
                "time": slot["time"],
                "phone": phone,
            },
        }
    )
    DEMO_BOOKINGS.append(
        {
            "chat_id": update.effective_chat.id,
            "name": context.user_data.get("booking_name", update.effective_user.full_name),
            "phone": phone,
            "service": service_name,
            "time": slot["time"],
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
    )

    await update.effective_message.reply_text(t(lang, "confirm"), reply_markup=client_menu_keyboard(lang))


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if "role" not in context.user_data or "lang" not in context.user_data:
        await start(update, context)
        return
    await show_menu(update, context)


def build_app(token: str) -> Application:
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    return application


def create_webhook_api(application: Application, webhook_path: str, webhook_full_url: str) -> FastAPI:
    api = FastAPI()

    @api.get("/health")
    async def health() -> Response:
        return Response(content="OK", status_code=status.HTTP_200_OK)

    @api.post(f"/{webhook_path}")
    async def telegram_webhook(request: Request) -> Response:
        payload = await request.json()
        update = Update.de_json(payload, application.bot)
        await application.process_update(update)
        return Response(content="OK", status_code=status.HTTP_200_OK)

    @api.on_event("startup")
    async def on_startup() -> None:
        await application.initialize()
        await application.start()
        await application.bot.set_webhook(webhook_full_url, allowed_updates=Update.ALL_TYPES)

    @api.on_event("shutdown")
    async def on_shutdown() -> None:
        await application.bot.delete_webhook()
        await application.stop()
        await application.shutdown()

    return api


def main() -> None:
    dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    load_dotenv(dotenv_path=dotenv_path)
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing. Set env var or add it in your shell.")

    app = build_app(token)
    webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL", "").strip()

    if webhook_url:
        webhook_port = int(os.getenv("PORT", os.getenv("TELEGRAM_WEBHOOK_PORT", "8080")))
        webhook_listen = os.getenv("TELEGRAM_WEBHOOK_LISTEN", "0.0.0.0")
        webhook_path = os.getenv("TELEGRAM_WEBHOOK_PATH", "").strip() or token
        webhook_full_url = f"{webhook_url.rstrip('/')}/{webhook_path}"

        logger.info(
            "Bot is running in webhook mode on %s:%s, webhook=%s, health=/health",
            webhook_listen,
            webhook_port,
            webhook_full_url,
        )
        api = create_webhook_api(app, webhook_path, webhook_full_url)
        uvicorn.run(api, host=webhook_listen, port=webhook_port)
        return

    logger.info("Bot is running in polling mode...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()




