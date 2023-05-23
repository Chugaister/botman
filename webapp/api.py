from flask import Flask
import config
from dotenv import load_dotenv
from os import getenv
from manager.manager import Manager
from aiogram import types
import asyncio

load_dotenv()

app = Flask(__name__)


def create_webhook_handler(bot_manager):
    async def handle_webhook(request):
        data = await request.json()
        update = types.Update.de_json(data)
        bot_token = update.message.bot.token
        _, dp = bot_manager.bot_dict[bot_token]
        await dp.process_update(update)
        return 'OK'

    return handle_webhook

class WebhookManager(Manager):
    def __init__(self, bot_tokens, webhook_url):
        super().__init__(bot_tokens)
        self.webhook_url = webhook_url

    async def set_webhook(self):
        for bot, _ in self.bot_dict.values():
            await bot.set_webhook(self.webhook_url)

async def on_startup():
    await bot_manager.set_webhook()

webhook_url = f'https://{config.HOST+config.PORT}'
bot_tokens = [getenv('BOT_TOKEN1')]
bot_manager = Manager(bot_tokens)
webhook_handler = create_webhook_handler(bot_manager)
app.route('/webhook', methods=['POST'])(webhook_handler)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(on_startup(bot_manager))
    app.run(
        host=config.HOST,
        port=config.PORT,
        ssl_context='adhoc'
    )