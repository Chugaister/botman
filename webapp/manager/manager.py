import logging
from aiogram import Bot, Dispatcher, types


class Manager:
    def __init__(self, bot_tokens):
        self.bot_dict = {token: (Bot(token=token), Dispatcher(Bot(token=token))) for token in bot_tokens}

        logging.basicConfig(level=logging.INFO)

        for bot, dp in self.bot_dict.values():
            self.register_handlers(dp)

    def register_handlers(self, dp):
        dp.register_message_handler(lambda message: self.echo(message, dp.bot))

    async def handle_message(self, message: types.Message):
        bot_token = message.bot.token
        bot, _ = self.bot_dict[bot_token]

        if message.text.startswith('/start'):
            await self.send_start_message(bot, message.chat.id)
        else:
            await self.echo_message(bot, message.chat.id, message.text)

    def on_startup(self):
        for bot, _ in self.bot_dict.values():
             bot.set_webhook("20.100.169.26")


    async def send_start_message(self, bot, chat_id):
        response_text = "Welcome to the bot! Send me a message and I'll echo it back."
        await bot.send_message(chat_id=chat_id, text=response_text)

    async def echo_message(self, bot, chat_id, message_text):
        await bot.send_message(chat_id=chat_id, text=message_text)

    