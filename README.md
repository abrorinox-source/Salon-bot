# Beauty Salon Demo Bot (Telegram)

CRM va adminga xabar yubormasdan ishlaydigan demo Telegram bot.

## Funksiyalar

- 3 tilda start: O'zbekcha, Русский, English
- Tilga mos asosiy menyu:
  - Services / Xizmatlar / Услуги
  - Book Appointment / Yozilish / Записаться
  - Ask a Question / Savol berish / Задать вопрос
- 3 ta xizmat va har biri ostida `Book Appointment` tugmasi
- To'liq booking flow:
  1. Xizmat tanlash
  2. Vaqt tanlash
  3. Ism kiritish
  4. Telefon yuborish (matn yoki kontakt)
  5. Tasdiqlash xabari
- Demo reminder: 90 soniyadan keyin avtomatik eslatma
- Ask a Question: avtomatik javob (adminga yuborilmaydi)

## O'rnatish

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Sozlash

1. `.env` fayl yarating (`.env.example` dan nusxa oling):

```powershell
Copy-Item .env.example .env
```

2. `.env` ichiga tokenni yozing:

```dotenv
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
```

3. Botni ishga tushiring:

```bash
python bot.py
```

## Webhook rejimi (ixtiyoriy)

`TELEGRAM_WEBHOOK_URL` berilsa bot polling o'rniga webhookda ishga tushadi.

`.env` misol:

```dotenv
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_WEBHOOK_URL=https://your-domain.com
TELEGRAM_WEBHOOK_PORT=8080
TELEGRAM_WEBHOOK_LISTEN=0.0.0.0
TELEGRAM_WEBHOOK_PATH=salon-hook
```

Izoh:
- `TELEGRAM_WEBHOOK_URL` bo'sh bo'lsa polling ishlaydi.
- `TELEGRAM_WEBHOOK_PATH` bo'sh bo'lsa path sifatida bot token ishlatiladi.
- Render'da `PORT` env avtomatik beriladi va bot shu portni ishlatadi.
- Health endpoint: `GET /health` -> `200 OK`

Render cron ping misol:

- URL: `https://<service-name>.onrender.com/health`
- Method: `GET`

## Eslatma

- Bu loyiha Telegram demo sifatida tayyorlangan.
- CRM yo'q.
- Adminga xabar yuborish yo'q.
- Reminder demo uchun 1-2 daqiqa o'rniga 90 soniya qilib qo'yilgan.
