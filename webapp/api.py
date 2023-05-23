from flask import Flask, send_file
import config
from dotenv import load_dotenv
from os import getenv
from manager.manager import Manager
from aiogram import types
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

bot_tokens = [getenv('BOT_TOKEN1')]
Manager.on_startup()
bot_manager = Manager(bot_tokens)
webhook_handler = create_webhook_handler(bot_manager)
app.route('/webhook', methods=['POST'])(webhook_handler)

if __name__ == "__main__":
    app.run(
        host=config.HOST,
        port=config.PORT,
        ssl_context='adhoc'
    )