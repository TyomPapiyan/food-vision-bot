# 🍽 FoodLens Bot

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python"/>
  <img src="https://img.shields.io/badge/aiogram-3.x-blue?style=for-the-badge&logo=telegram"/>
  <img src="https://img.shields.io/badge/Gemini-2.0 Flash-orange?style=for-the-badge&logo=google"/>
  <img src="https://img.shields.io/badge/SQLite-aiosqlite-green?style=for-the-badge&logo=sqlite"/>
</p>

> **FoodLens** is a Telegram bot that analyzes food photos using Google Gemini AI — identifies the dish, calculates nutrition facts (calories, protein, fat, carbs) and generates a step-by-step recipe. Supports 🇷🇺 Russian, 🇬🇧 English and 🇦🇲 Armenian.

---

## ✨ Features

- 📸 **Food photo analysis** — send any food photo, get instant results
- 🔥 **Nutrition facts** — calories, protein, fat, carbs per portion
- 📖 **Auto recipe generation** — step-by-step recipe for the identified dish
- 📊 **Food diary** — tracks everything you eat today
- 💳 **Subscription system** — via Telegram Stars (30 / 90 / 365 days)
- 🆓 **Free tier** — 3 free scans per day, resets every midnight
- 🎁 **Promo codes** — admin can create codes for free subscription days
- 🔗 **Referral system** — invite a friend, get 1 month free
- 🌐 **3 languages** — Russian, English, Armenian
- 🛡 **Admin panel** — stats, broadcast, manual subscription grant

---

## 📁 Project Structure

```
foodlens-bot/
├── bot.py                  # Entry point, polling, expiry notifications
├── .env                    # Secrets (not committed)
├── requirements.txt
├── privacy_policy.md
│
├── handlers/
│   ├── start.py            # /start, language selection, referral handling
│   ├── photo.py            # Photo analysis, daily scan limit logic
│   ├── menu.py             # All menu buttons + /me /ref /promo /cancel
│   ├── admin.py            # /admin /give /createpromo /broadcast
│   └── payment.py          # Telegram Stars invoice + payment confirmation
│
├── services/
│   ├── vision.py           # Gemini vision — identifies dish from photo
│   ├── nutrition.py        # Gemini — returns nutrition JSON
│   └── recipe.py           # Gemini — generates recipe in user's language
│
├── keyboards/
│   └── main_kb.py          # All keyboards (main menu, result, subscription, language)
│
├── locales/
│   ├── __init__.py         # t(lang, key) helper
│   ├── ru.py               # Russian strings
│   ├── en.py               # English strings
│   └── hy.py               # Armenian strings
│
└── database/
    └── db.py               # All DB logic (users, food_log, subscriptions, promos, refs)
```

---

## ⚙️ Environment Variables

Create a `.env` file in the root directory:

```env
TELEGRAM_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_google_gemini_api_key
ADMIN_ID=your_telegram_user_id
```

| Variable | Description |
|----------|-------------|
| `TELEGRAM_TOKEN` | Get from [@BotFather](https://t.me/BotFather) |
| `GEMINI_API_KEY` | Get from [Google AI Studio](https://aistudio.google.com) |
| `ADMIN_ID` | Your Telegram user ID (use [@userinfobot](https://t.me/userinfobot)) |

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/TyomPapiyan/foodlens-bot.git
cd foodlens-bot
```

### 2. Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Fill in your tokens in .env
```

### 5. Run the bot

```bash
python bot.py
```

---

## 📦 Requirements

```
aiogram==3.x
aiosqlite
google-genai
python-dotenv
```

---

## 💳 Subscription Plans

| Plan | Price | Duration |
|------|-------|----------|
| Monthly | 250 ⭐ Stars | 30 days |
| Quarterly | 600 ⭐ Stars | 90 days |
| Yearly | 2000 ⭐ Stars | 365 days |

Payments are handled entirely by Telegram Stars — no external payment gateway needed.

---

## 🛡 Admin Commands

| Command | Description |
|---------|-------------|
| `/admin` | View bot statistics |
| `/give <user_id> <days>` | Grant subscription manually |
| `/createpromo <code> <days> <max_uses>` | Create promo code |
| `/broadcast <text>` | Send message to all users |

---

## 🗄 Database Schema

```
users          — user_id, language, created_at, referred_by
food_log       — user_id, dish_name, calories, protein, fat, carbs, logged_at
subscriptions  — user_id, is_active, expires_at, scans_used
promo_codes    — code, days, max_uses, uses_count, created_at
promo_uses     — user_id, code, used_at
```

---

## 🌐 Localization

The bot supports 3 languages selectable on first launch:

| Language | Code |
|----------|------|
| 🇷🇺 Russian | `ru` |
| 🇬🇧 English | `en` |
| 🇦🇲 Armenian | `hy` |

To add a new language — create `locales/xx.py` with the same keys as `locales/en.py` and register it in `locales/__init__.py`.

---

## 📊 How It Works

```
User sends photo
      ↓
Check daily free scan limit (3/day) or subscription
      ↓
Gemini Vision — identifies dish, estimates portion
      ↓
Gemini — calculates nutrition facts (parallel)
Gemini — generates recipe (parallel)
      ↓
Bot replies with dish name, KBJU, recipe
      ↓
User can save to food diary
```

---

## 📜 Privacy

Food photos are sent to Google Gemini API for analysis only and are **not stored** on our servers. See [privacy_policy.md](./privacy_policy.md) for full details.

---

## 👤 Author

Made by [@TyomPapiyan](https://t.me/TyomPapiyan)

---

## 📄 License

MIT License — feel free to use, modify and distribute.