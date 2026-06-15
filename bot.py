import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, ADMIN_IDS
from database import create_tables
from middlewares import DatabaseMiddleware, ActiveUserMiddleware
from handlers import (
    start_router,
    subscription_router,
    user_router,
    tasks_router,
    bonuses_router,
    withdraw_router,
    admin_router,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    # Initialize database
    logger.info("Initializing database...")
    await create_tables()
    logger.info("Database initialized successfully!")

    # Initialize bot and dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Register middlewares
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    dp.message.middleware(ActiveUserMiddleware())
    dp.callback_query.middleware(ActiveUserMiddleware())

    # Register routers (order matters!)
    dp.include_router(start_router)
    dp.include_router(subscription_router)
    dp.include_router(admin_router)
    dp.include_router(withdraw_router)
    dp.include_router(tasks_router)
    dp.include_router(bonuses_router)
    dp.include_router(user_router)

    # Notify all admins on startup
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "✅ <b>BonusCoin Bot ishga tushdi!</b>")
        except Exception:
            pass

    logger.info("Bot started!")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())