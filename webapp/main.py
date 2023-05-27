from fastapi import FastAPI
from aiogram import types, Dispatcher, Bot
from bot import dp, bot, TOKEN




app = FastAPI()
WEBHOOK_PATH = f"/"
WEBHOOK_URL = "https://791b-213-48-5-122.eu.ngrok.io" + WEBHOOK_PATH


@app.on_event("startup")
async def on_startup():
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URL:
        await bot.set_webhook(
            url=WEBHOOK_URL
        )


@app.post(WEBHOOK_PATH)
async def bot_webhook(update: dict):
    telegram_update = types.Update(**update)
    Dispatcher.set_current(dp)
    Bot.set_current(bot)
    await dp.process_update(telegram_update)


@app.on_event("shutdown")
async def on_shutdown():
    print("shutting down...")
    await bot.delete_webhook()
    await bot.session.close()