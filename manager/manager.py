import logging
from aiogram import Bot, Dispatcher, types
from data import models
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from web_config.local_config import PUBLIC_IP
from userbot.handlers import start_handler, req_handler, captcha_confirm, CaptchaStatesGroup


class Manager:
    def __init__(self, bots: list[models.Bot]):
        self.bot_dict = {bot.token: (Bot(token=bot.token), Dispatcher(Bot(token=bot.token), storage=MemoryStorage())) for bot in bots}

        logging.basicConfig(level=logging.INFO)
        
    def register_handlers(self, bots: list[models.Bot]):
        for bot in bots:
            if bot.token not in self.bot_dict.keys():
                self.bot_dict[bot.token] = (Bot(token=bot.token), Dispatcher(Bot(token=bot.token), storage=MemoryStorage()))
        for bot, dp in self.bot_dict.values():
            Bot.set_current(bot)
            Dispatcher.set_current(dp)
            # dp.register_message_handler(lambda message: self.echo_message(Bot.get_current(), message))
            dp.register_message_handler(lambda msg: start_handler(Bot.get_current(), Dispatcher.get_current(), msg), commands="start")
            dp.register_chat_join_request_handler(lambda req, state: req_handler(Bot.get_current(), Dispatcher.get_current(), req, state))
            dp.register_message_handler(lambda msg, state: captcha_confirm(Bot.get_current(), Dispatcher.get_current(), msg, state), state=CaptchaStatesGroup.captcha)

    async def set_webhook(self, bots: list[models.Bot]):
        for bot in bots:
            if bot.token not in self.bot_dict.keys():
                self.bot_dict[bot.token] = ((Bot(token=bot.token)), Dispatcher(Bot(token=bot.token)))  
            ubot = Bot(token=bot.token)
            await ubot.set_webhook(f"https://{PUBLIC_IP}/bot/{bot.token}")
            await (await ubot.get_session()).close()

    async def delete_webhook(self, bot: models.Bot):
        ubot = Bot(bot.token)
        await ubot.delete_webhook()
        await ubot.session.close()

    async def delete_webhooks(self, bots: list[models.Bot]):
        for bot in bots:
            await self.delete_webhook(bot)

    async def echo_message(self, bot, message: types.Message):
        await message.answer(message.text)

    