import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

from handlers.start import router as start_router
from handlers.photo import router as photo_router
from handlers.menu import router as menu_router
from handlers.admin import router as admin_router
from handlers.payment import router as payment_router
from database.db import init_db, get_expiring_soon, get_user_language
from locales import t

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def notify_expiring(bot: Bot):
    while True:
        try:
            expiring = await get_expiring_soon(days_before=3)
            for user_id, expires_at in expiring:
                try:
                    lang = await get_user_language(user_id)
                    expires = datetime.fromisoformat(expires_at)
                    expires_str = expires.strftime("%d.%m.%Y")
                    await bot.send_message(
                        user_id,
                        t(lang, "expiry_notify").format(date=expires_str),
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Ошибка в notify_expiring: {e}")
        await asyncio.sleep(60 * 60 * 12)


async def main():
    bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start_router)
    dp.include_router(payment_router)  # payment раньше menu — чтобы перехватывал sub_ callbacks
    dp.include_router(photo_router)
    dp.include_router(menu_router)
    dp.include_router(admin_router)

    await init_db()

    logger.info("FoodLens bot запущен!")

    asyncio.create_task(notify_expiring(bot))

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("FoodLens bot остановлен.")
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass