from flask import Flask, send_file
import config
from dotenv import load_dotenv
from os import getenv
import sys
sys.path.insert(0, 'botman\manager')
from manager import Manager
from aiogram import types
load_dotenv()

app = Flask(__name__)


# @app.route('/<token>', methods=['POST'])
# def handle_webhook(token):
#     data = request.get_json()
#     update = types.Update.de_json(data)
#     bot_token = update.message.bot.token
#     bot, dp = bot_manager.bot_dict[bot_token]
#     dp.process_update(update)
#     return "OK"


def create_webhook_handler(bot_manager):
    async def handle_webhook(request):
        data = await request.json()
        update = types.Update.de_json(data)
        bot_token = update.message.bot.token
        bot, dp = bot_manager.bot_dict[bot_token]
        await dp.process_update(update)
        return 'OK'

    return handle_webhook

@app.route(f"/.well-known/pki-validation/{config.auth_file_name}")
def send_auth_file():
    return send_file(config.auth_file_name)


if __name__ == "__main__":
    bot_tokens = [getenv('BOT_TOKEN1')]
    bot_manager = Manager(bot_tokens)
    webhook_handler = create_webhook_handler(bot_manager)
    app.route('/webhook', methods=['POST'])(webhook_handler)
    app.run(
        host=config.HOST,
        port=config.PORT,
        ssl_context='adhoc'
    )