import asyncio
import logging
from aiogram import Bot, Dispatcher
from bot.handlers import start, record, help, admin, info


async def main():
    bot = Bot(token='7822443255:AAFM_JCzysQSqBGItQOtnzOdKp5Mak0PO5c')
    dp = Dispatcher()
    dp.include_routers(start.router, help.router, record.router, admin.admin_router, info.router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Осуществлен выход.')