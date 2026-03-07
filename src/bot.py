import asyncio
from aiogram import Bot, Dispatcher
from conf.logging.file_opening import LOG_FILE_PATH, LOG_FILE_ENCODING
from config import config
import logging
from handlers import common,homework_handler,schedule_handler,ai_handler,dev_handler,achievments_handler
async def main():
    bot = Bot(token=config.bot_token.get_secret_value())
    dp = Dispatcher()
    asyncio.create_task(schedule_handler.update_data_task())
    dp.include_routers(common.router,
                       ai_handler.router,
                       schedule_handler.router,
                       homework_handler.router,
                       achievments_handler.router,
                       dev_handler.router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        filename=LOG_FILE_PATH,
        encoding = LOG_FILE_ENCODING
    )
    logging.getLogger("aiogram").setLevel(logging.INFO)
    asyncio.run(main())
    logging.info("Bot runned")