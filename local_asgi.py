from fastapi import FastAPI
from aiogram import types, Dispatcher, Bot
import uvicorn
from web_config.local_config import PUBLIC_IP
from bot.misc import bot as main_bot, dp as main_dp
from bot.config import token as main_token
from bot.misc import manager as bot_manager, bots_db
import bot.handlers


app = FastAPI()


@app.on_event("startup")
async def on_startup():
    await main_bot.set_webhook(url=f"https://{PUBLIC_IP}/bot/{main_token}")
    ubots = bots_db.get_by(status=1)
    bot_manager.register_handlers(ubots)
    await bot_manager.set_webhook(ubots)


@app.post("/bot/{token}")
async def bot_webhook(token, update: dict):
    telegram_update = types.Update(**update)
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
    await bot_manager.delete_webhooks(bots_db.get_all())


from web_config.local_config import PORT, HOST, PUBLIC_IP


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=HOST,
        port=PORT
    )