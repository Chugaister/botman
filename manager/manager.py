import logging
from aiogram import Bot, Dispatcher, types
from data import models

from web_config.config import PUBLIC_IP
from userbot.handlers import start_handler, req_handler, captcha_confirm, CaptchaStatesGroup


class Manager:
    def __init__(self, bots: list[models.Bot]):
        self.bot_dict = {bot.token: (Bot(token=bot.token), Dispatcher(Bot(token=bot.token))) for bot in bots}

        logging.basicConfig(level=logging.INFO)

        for bot, dp in self.bot_dict.values():
             dp.register_message_handler(lambda message: self.echo_message(bot, message))
             dp.register_message_handler(lambda msg: start_handler(bot, dp, msg), commands="start")
             dp.register_chat_join_request_handler(lambda req, state: req_handler(bot, dp, req, state))
             dp.register_message_handler(lambda msg, state: captcha_confirm(bot, dp, msg, state), state=CaptchaStatesGroup.captcha)

    async def set_webhook(self, bots: list[models.Bot]):
        for bot in bots:
            ubot = Bot(token=bot.token)
            await ubot.set_webhook(f"https://{PUBLIC_IP}/bot/{bot.token}")
            await (await ubot.get_session()).close()

    async def echo_message(self, bot, message: types.Message):
        await message.answer(message.text)

    