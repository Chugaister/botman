from aiogram import Bot, Dispatcher, types
from data import models
from aiogram.utils.exceptions import Unauthorized
from aiogram.contrib.fsm_storage.memory import MemoryStorage
# from web_config.local_config import PUBLIC_IP
from data.factory import *
from userbot.handlers import start_handler, req_handler, captcha_confirm, CaptchaStatesGroup
import logging
class Manager:
    def __init__(self, bots: list[models.Bot], webhook_host: str):
        self.sessions = []
        self.logger = logging.getLogger('aiogram')
        self.bot_dict = {bot.token: (Bot(token=bot.token), Dispatcher(Bot(token=bot.token), storage=MemoryStorage())) for bot in bots}
        self.webhook_host = webhook_host
    def register_handlers(self, bots: list[models.Bot]):
        for bot in bots:
            if bot.token not in self.bot_dict.keys():
                self.bot_dict[bot.token] = (Bot(token=bot.token, parse_mode="HTML"), Dispatcher(Bot(token=bot.token), storage=MemoryStorage()))
        for bot, dp in self.bot_dict.values():
            Bot.set_current(bot)
            Dispatcher.set_current(dp)
            # dp.register_message_handler(lambda message: self.echo_message(Bot.get_current(), message))
            dp.register_message_handler(lambda msg: start_handler(Bot.get_current(), Dispatcher.get_current(), msg), commands="start")
            dp.register_chat_join_request_handler(lambda req, state: req_handler(Bot.get_current(), Dispatcher.get_current(), req, state))
            dp.register_message_handler(lambda msg, state: captcha_confirm(Bot.get_current(), Dispatcher.get_current(), msg, state), state=CaptchaStatesGroup.captcha)
            dp.register_errors_handler(self.log_exception)
    async def set_webhook(self, bots: list[models.Bot]):
        for bot in bots:
            if bot.token not in self.bot_dict.keys():
                self.bot_dict[bot.token] = ((Bot(token=bot.token)), Dispatcher(Bot(token=bot.token)))  
            ubot = Bot(token=bot.token)
            self.sessions.append(await ubot.get_session())
            try:
                await ubot.set_webhook(f"https://{self.webhook_host}/bot/{bot.token}", drop_pending_updates=True)
            except Unauthorized:
                bot = await bots_db.get(ubot.id)
                bot.admin = None
                await bots_db.update(bot)
    async def delete_webhook(self, bot: models.Bot):
        try:
            ubot = self.bot_dict[bot.token][0]
        except KeyError:
            ubot = Bot(token=bot.token)
        try:
            await (await ubot.get_session()).close()
            await ubot.delete_webhook()
        except Unauthorized:
            bot = await bots_db.get(ubot.id)
            bot.admin = None
            await bots_db.update(bot)
        

    async def delete_webhooks(self, bots: list[models.Bot]):
        for bot in bots:
            await self.delete_webhook(bot)

    async def log_exception(self, update: types.Update, exception: Exception):
        self.logger.error(f"An error occurred in update {update.update_id}: {exception}", exc_info=True)

    async def echo_message(self, bot, message: types.Message):
        await message.answer(message.text)

    