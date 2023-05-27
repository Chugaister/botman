import logging
from aiogram import Bot, Dispatcher, types


class Manager:
    def __init__(self, bot_tokens: list[str]):
        self.bot_dict = {token: (Bot(token=token), Dispatcher(Bot(token=token))) for token in bot_tokens}

        logging.basicConfig(level=logging.INFO)

        for bot, dp in self.bot_dict.values():
             dp.register_message_handler(lambda message: self.echo_message(bot, message))

    async def echo_message(self, bot, message: types.Message):
        await message.answer(message.text)

    