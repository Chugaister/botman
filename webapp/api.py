from flask import Flask
import config
from dotenv import load_dotenv
from os import getenv
from manager.manager import Manager
from aiogram import types, Dispatcher, Bot
import asyncio

load_dotenv()

app = Flask(__name__)




class WebhookManager(Manager):
    def __init__(self, bot_tokens, webhook_url):
        super().__init__(bot_tokens)
        self.webhook_url = webhook_url

    async def set_webhook(self):
        for bot, _ in self.bot_dict.values():
            await bot.set_webhook(self.webhook_url)

async def on_startup():
    await bot_manager.register_handlers()
    await bot_manager.set_webhook()

def create_webhook_handler(bot_manager):
    async def handle_webhook(request):
        data = await request.json()
        update = types.Update.de_json(data)
        bot_token = update.message.bot.token
        bot, dp = bot_manager.bot_dict[bot_token]
        Dispatcher.set_current(dp)
        Bot.set_current(bot)
        await dp.process_update(update)
        return 'OK'

    return handle_webhook

webhook_url = f'https://20.100.169.126/webhook'
bot_tokens = [getenv('BOT_TOKEN1')]
bot_manager = Manager(bot_tokens)
webhook_handler = create_webhook_handler(bot_manager)
app.route('/webhook', methods=['POST'])(webhook_handler)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(on_startup())
    app.run(
        host=config.HOST,
        port=config.PORT,
        ssl_context='adhoc'
    )