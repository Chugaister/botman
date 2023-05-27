from fastapi import FastAPI
from dotenv import load_dotenv
from os import getenv
from aiogram import types, Dispatcher, Bot

load_dotenv()

bot_tokens = [getenv("BOT_TOKEN1"), getenv("BOT_TOKEN2")]
from manager.manager import Manager


bot_manager = Manager(bot_tokens=bot_tokens)

app = FastAPI()



@app.on_event("startup")
async def on_startup():
    for token, (_, bot) in bot_manager.bot_dict.items():
        WEBHOOK_PATH = f"/bot/{token}"
        WEBHOOK_URL = "https://20.100.169.126" + WEBHOOK_PATH
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url != WEBHOOK_URL:
            await bot.set_webhook(
                url=WEBHOOK_URL
            )


@app.post("/bot/{token}")
async def bot_webhook(token, update: dict):
    dp, bot = bot_manager.bot_dict[token]
    telegram_update = types.Update(**update)
    Dispatcher.set_current(dp)
    Bot.set_current(bot)
    await dp.process_update(telegram_update)


@app.on_event("shutdown")
async def on_shutdown():
    print("shutting down...")
    for _, bot in bot_manager.bot_dict.values():
        await bot.delete_webhook()
        await bot.session.close()