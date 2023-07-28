from logging.handlers import TimedRotatingFileHandler
from aiogram import types, Dispatcher, Bot
from aiogram.types.bot_command import BotCommand
import uvicorn
from fastapi import FastAPI
import argparse
import logging
import sys
import os
import colorama
from bot.misc import bot as main_bot, dp as main_dp
from bot.config import token as main_token
from bot.misc import manager as bot_manager, bots_db
from bot.listeners import run_listeners
import bot.handlers

parser = argparse.ArgumentParser()
parser.add_argument('--local', action='store_true', help='Run in local mode')
parser.add_argument('--port', action='store', help='Select the port to run on')
parser.add_argument('--token', action='store', help='Bot token to run on')
args = parser.parse_args()
if args.local:
    from web_config.local_config import WEBHOOK_HOST, PUBLIC_IP, HOST, PORT
else:
    from web_config.config import WEBHOOK_HOST, PUBLIC_IP, HOST, PORT
    if args.port:
        PORT = args.port
        print(PORT)

colorama.init()
current_dir = os.path.dirname(os.path.abspath(__file__))
log_directory = os.path.join(current_dir, "logs")
log_file = os.path.join(log_directory, "logfile.log")
os.makedirs(log_directory, exist_ok=True)
# logging.basicConfig(
#     filename=log_file,
#     level=logging.INFO,
#     format='%(asctime)s %(levelname)s:%(message)s',
#     encoding='utf-8'
# )

aiogram_logger = logging.getLogger("aiogram")
aiogram_logger.setLevel(logging.DEBUG)

file_handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7, encoding='utf-8')
file_handler.suffix = "%Y-%m-%d_%H-%M-%S"  # Add a suffix based on the date
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

aiogram_logger.addHandler(file_handler)
def custom_exception_handler(exc_type, exc_value, exc_traceback):
    aiogram_logger.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))




sys.excepthook = custom_exception_handler


async def log_exception(update: types.Update, exception: Exception):
    aiogram_logger.error(f"An error occurred in update {update.update_id}: {exception}", exc_info=True)

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    allowed_updates = ["message", "chat_join_request", "callback_query"]
    await main_bot.set_my_commands(
        commands=[
            BotCommand("start", "перезапустити сервіс"),
            BotCommand("mybots", "меню ботів")
            # BotCommand("premium", "інформація про преміум")
        ]
    )
    await main_bot.set_webhook(
        url=f"https://{WEBHOOK_HOST}/bot/{main_token}",
        drop_pending_updates=True,
        allowed_updates=allowed_updates
    )
    ubots = await bots_db.get_by(status=1)
    ubots = [ubot for ubot in ubots if ubot.admin is not None]
    main_dp.register_errors_handler(log_exception)
    bot_manager.register_handlers(ubots)
    await bot_manager.set_webhook(ubots)
    await run_listeners()


@app.post("/bot/{token}")
async def bot_webhook(token, update: dict):
    telegram_update = types.Update(**update)
    aiogram_logger.debug(f"Get updates: {telegram_update}")
    if token == main_token:
        Dispatcher.set_current(main_dp)
        Bot.set_current(main_bot)
        await main_dp.process_update(telegram_update)
    else:
        ubot, udp = bot_manager.bot_dict[token]
        Dispatcher.set_current(udp)
        Bot.set_current(ubot)
        await udp.process_update(telegram_update)


@app.on_event("shutdown")
async def on_shutdown():
    await main_bot.delete_webhook()
    await bot_manager.delete_webhooks(await bots_db.get_all())


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
