import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
ADMIN_IDS = [5474786905, 6332560971, 8382123647]

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "bonus_coin_bot")

BOT_USERNAME = os.getenv("BOT_USERNAME", "BonusCoinBot")
MIN_WITHDRAW = int(os.getenv("MIN_WITHDRAW", "10000"))
REFERRAL_BONUS = int(os.getenv("REFERRAL_BONUS", "100"))

DATABASE_URL = "sqlite+aiosqlite:///bonus_coin_bot.db"

# Referral milestone bonuses
REFERRAL_MILESTONES = {
    10: 1000,
    50: 7000,
    100: 20000,
}
