import os
import uvicorn
from web_config.config import PORT, HOST, PUBLIC_IP
# from app import app
from fastapi import FastAPI
from aiogram import types, Dispatcher, Bot
from bot.misc import bot as main_bot, dp as main_dp
from bot.config import token as main_token
from bot.misc import manager as bot_manager, bots_db
from bot.listeners import listen_mails, listen_purges, listen_autodeletion
import bot.handlers
from asyncio import create_task
import argparse
import logging
import sys
parser = argparse.ArgumentParser()
parser.add_argument('--local', action='store_true', help='Run in local mode')

args = parser.parse_args()
if args.local:
    from web_config.local_config import PUBLIC_IP, HOST, PORT
else:
    from web_config.config import PUBLIC_IP, HOST, PORT

logging.basicConfig(filename='logs/logfile.logs', level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s', encoding='utf-8')
def custom_exception_handler(exc_type, exc_value, exc_traceback):
    logging.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))

# Set the custom exception hook
sys.excepthook = custom_exception_handler


async def log_exception(update: types.Update, exception: Exception):
        logging.error(f"An error occurred in update {update.update_id}: {exception}", exc_info=True)

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    await main_bot.set_webhook(url=f"https://{PUBLIC_IP}/bot/{main_token}", drop_pending_updates=True)
    ubots = await bots_db.get_by_fromDB(status=1)
    main_dp.register_errors_handler(log_exception)
    bot_manager.register_handlers(ubots)
    await bot_manager.set_webhook(ubots)
    create_task(listen_mails())
    create_task(listen_purges())
    create_task(listen_autodeletion())


@app.post("/bot/{token}")
async def bot_webhook(token, update: dict):
    telegram_update = types.Update(**update)
    logging.debug(f"Get updates: {telegram_update}")
    if token == main_token:
        Dispatcher.set_current(main_dp)
        Bot.set_current(main_bot)
        await main_dp.process_update(telegram_update)
    else:
        bot, dp = bot_manager.bot_dict[token]
        Dispatcher.set_current(dp)
        Bot.set_current(bot)
        await dp.process_update(telegram_update)


@app.on_event("shutdown")
async def on_shutdown():
    await main_bot.delete_webhook()
    await bot_manager.delete_webhooks(await bots_db.get_all_fromDB())


certfile_path = os.path.join(os.path.dirname(__file__), "web_config", PUBLIC_IP, "certificate.crt")
keyfile_path = os.path.join(os.path.dirname(__file__), "web_config", PUBLIC_IP, "private.key")
ca_bundle_path = os.path.join(os.path.dirname(__file__), "web_config", PUBLIC_IP, "ca_bundle.crt")

if __name__ == "__main__":
    if args.local:
        uvicorn.run(
        app,
        host=HOST,
        port=PORT
        )
    else:
        uvicorn.run(
            app,
            host=HOST,
            port=PORT,
            ssl_certfile=certfile_path,
            ssl_keyfile=keyfile_path,
            ssl_ca_certs=ca_bundle_path
        )