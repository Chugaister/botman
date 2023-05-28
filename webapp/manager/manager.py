import logging
from aiogram import Bot, Dispatcher, types
from data import models

class Manager:
    def __init__(self, bots: list[models.Bot]):
        self.bot_dict = {bot.token: (Bot(token=bot.token), Dispatcher(Bot(token=bot.token))) for bot in bots}

        logging.basicConfig(level=logging.INFO)

        for bot, dp in self.bot_dict.values():
             dp.register_message_handler(lambda message: self.echo_message(bot, message))

    async def echo_message(self, bot, message: types.Message):
        await message.answer(message.text)

    