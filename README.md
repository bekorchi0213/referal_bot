# 🤖 BonusCoin Telegram Bot

Python + Aiogram 3.x + MySQL asosida qurilgan professional referal bot.

## 📋 Xususiyatlar

- ✅ Referal tizimi (milestone bonuslar bilan)
- ✅ Majburiy kanal obunasi
- ✅ Kunlik topshiriqlar
- ✅ Reyting tizimi
- ✅ Promo kodlar
- ✅ Mablag' yechish tizimi
- ✅ To'liq admin panel
- ✅ FSM (Finite State Machine) bilan qurilgan
- ✅ SQLAlchemy ORM + MySQL

## 🚀 O'rnatish

### 1. Loyihani yuklab olish

```bash
git clone <repo>
cd bonus_coin_bot
```

### 2. Virtual muhit

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# yoki
venv\Scripts\activate  # Windows
```

### 3. Kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt
```

### 4. MySQL ma'lumotlar bazasini sozlash

```sql
CREATE DATABASE bonus_coin_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. `.env` faylini to'ldirish

```env
BOT_TOKEN=your_token_here
ADMIN_ID=your_telegram_id
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=bonus_coin_bot
BOT_USERNAME=YourBotUsername
MIN_WITHDRAW=10000
REFERRAL_BONUS=100
```

### 6. Botni ishga tushirish

```bash
python bot.py
```

## 🌐 Render.com ga Deploy qilish

1. GitHub reposiga yuklang
2. Render.com da yangi **Worker** service yarating
3. `render.yaml` fayli avtomatik taniladi
4. Environment variables ni sozlang
5. **MySQL** uchun PlanetScale yoki Railway ishlatish mumkin

## 📁 Fayl tuzilishi

```
bonus_coin_bot/
├── bot.py                  # Asosiy fayl
├── config.py               # Sozlamalar
├── requirements.txt        # Kutubxonalar
├── render.yaml             # Deploy config
├── .env                    # Muhit o'zgaruvchilari
├── database/
│   ├── __init__.py
│   ├── models.py           # SQLAlchemy modellari
│   ├── session.py          # DB sessiya
│   └── queries.py          # DB so'rovlar
├── handlers/
│   ├── __init__.py
│   ├── start.py            # /start handler
│   ├── subscription.py     # Obuna tekshirish
│   ├── user.py             # Asosiy foydalanuvchi
│   ├── tasks.py            # Topshiriqlar
│   ├── bonuses.py          # Bonuslar & promo
│   ├── withdraw.py         # Yechish
│   └── admin.py            # Admin panel
├── keyboards/
│   ├── __init__.py
│   └── keyboards.py        # Barcha klaviaturalar
├── middlewares/
│   ├── __init__.py
│   └── middleware.py       # DB & user middleware
├── states/
│   ├── __init__.py
│   └── states.py           # FSM holatlar
└── utils/
    ├── __init__.py
    └── helpers.py          # Yordamchi funksiyalar
```

## 🎯 Bot buyruqlari

- `/start` — Botni ishga tushirish
- `/admin` — Admin panel (faqat adminlar uchun)

## 💰 Referal tizimi

| Milestone | Bonus |
|-----------|-------|
| Har 1 referal | +100 ball |
| 10 referal | +1,000 ball |
| 50 referal | +7,000 ball |
| 100 referal | +20,000 ball |

## 📞 Muallif

Bot @BonusCoinBot uchun yaratilgan.
