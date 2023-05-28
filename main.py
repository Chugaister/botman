from fastapi import FastAPI
from aiogram import types, Dispatcher, Bot
from webapp.config import BOT_TOKEN1, BOT_TOKEN2
from bot.misc import bot as main_bot, dp as main_dp
from bot.config import token as main_token
bot_tokens = [BOT_TOKEN1, BOT_TOKEN2]
from bot.misc import manager as bot_manager



app = FastAPI()



@app.on_event("startup")
async def on_startup():
    await main_bot.set_webhook(url=f"https://20.100.169.126/bot/{main_token}")
    # for token, (bot, _) in bot_manager.bot_dict.items():
    #     WEBHOOK_PATH = f"/bot/{token}"
    #     WEBHOOK_URL = "https://20.100.169.126" + WEBHOOK_PATH
    #     webhook_info = await bot.get_webhook_info()
    #     if webhook_info.url != WEBHOOK_URL:
    #         await bot.set_webhook(
    #             url=WEBHOOK_URL
    #         )
    


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
    for bot, _ in bot_manager.bot_dict.values():
        await bot.delete_webhook()
        await bot.session.close()