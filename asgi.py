from logging.handlers import RotatingFileHandler
from aiogram import types, Dispatcher, Bot
from aiogram.types.bot_command import BotCommand
import uvicorn
from fastapi import FastAPI, HTTPException  
from fastapi.responses import FileResponse
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
from bot.config import secret_key
import datetime

parser = argparse.ArgumentParser()
parser.add_argument('--local', action='store_true', help='Run in local mode')
parser.add_argument('--port', action='store', help='Select the port to run on')
parser.add_argument('--token', action='store', help='Bot token to run on')
parser.add_argument('--source', action='store', help='Database folder path')
parser.add_argument('--logs', action='store', help='Logs folder path')
args = parser.parse_args()
if args.local:
    from web_config.local_config import WEBHOOK_HOST, PUBLIC_IP, HOST, PORT
else:
    from web_config.config import WEBHOOK_HOST, PUBLIC_IP, HOST, PORT
    if args.port:
        PORT = int(args.port)

colorama.init()
current_dir = os.path.dirname(os.path.abspath(__file__))
if args.logs:
    log_directory = os.path.join(current_dir, f'{args.logs}')
    log_file = os.path.join(log_directory, "logfile.log")
    os.makedirs(log_directory, exist_ok=True)
else:
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

max_log_size = 100 * 1024 * 1024


file_handler = RotatingFileHandler(log_file, maxBytes=max_log_size, backupCount=25, encoding='utf-8')
file_handler.suffix = "%Y-%m-%d_%H-%M-%S"  
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

aiogram_logger.addHandler(file_handler)
def custom_exception_handler(exc_type, exc_value, exc_traceback):
    aiogram_logger.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))


def list_files_and_last_modified(directory_path):
    file_list = []
    
    with os.scandir(directory_path) as entries:
        for entry in entries:
            if entry.is_file():
                last_modified = datetime.datetime.fromtimestamp(entry.stat().st_mtime)
                formatted_date = last_modified.strftime('%Y-%m-%d %H:%M:%S')
                
                file_info = {
                    "File": entry.name,
                    "Last Modified": formatted_date
                }
                file_list.append(file_info)

    return file_list


sys.excepthook = custom_exception_handler


async def log_exception(update: types.Update, exception: Exception):
    aiogram_logger.error(f"An error occurred in update {update.update_id}: {exception}", exc_info=True)

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    bot_manager.updates[main_token] = ""
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

@app.get('/logs/{key}/{id}')
def sendLogs(key, id):
    try:
        if key == secret_key:
            if int(id) > 0:
                file_path = f'{log_file}.{id}'
            elif int(id) == 0:
                file_path = f'{log_file}'
            return FileResponse(path=file_path, filename=file_path, media_type='text/plain')
        else:
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        return e

@app.get('/logsInfo/{key}')
def sendLogsInfo(key):
    try:
        if key == secret_key:
            return list_files_and_last_modified(log_directory)
        else: 
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        pass
    
@app.post("/bot/{token}")
async def bot_webhook(token, update: dict):
    telegram_update = types.Update(**update)
    if bot_manager.updates[token] == telegram_update["update_id"]:
        return
    bot_manager.updates[token] = telegram_update["update_id"]
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
    main_session = await main_bot.get_session()
    if main_session:
        try:
            await main_session.close()
        except Exception:
            pass
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
