import asyncio
import logging
from aiogram import Bot, Dispatcher
from settings.settings import settings
from handlers.basic import router
from database.db import init_db


async def on_start():
    # Инициализация бота и диспетчера
    bot = Bot(token=settings.bots.token)
    dp = Dispatcher()

    # Включение маршрутизаторов
    dp.include_router(router)

    try:
        logging.info('Бот запущен')
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logging.exception(f'Произошла ошибка: {e}')
    finally:
        await bot.session.close()

async def main():
    await init_db()

    await on_start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    asyncio.run(main())
