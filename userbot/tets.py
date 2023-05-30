from aiogram import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from userbot.handlers import *


ubot = Bot("6278692895:AAE0nxA6w7YVbVVOcN9UJh33IHvhoQQ91Mg")
ustorage = MemoryStorage()
udp = Dispatcher(ubot, storage=ustorage)

udp.register_message_handler(lambda msg: start_handler(ubot, udp, msg), commands="start")
udp.register_chat_join_request_handler(lambda req, state: req_handler(ubot, udp, req, state))
udp.register_message_handler(lambda msg, state: captcha_confirm(ubot, udp, msg, state), state=CaptchaStatesGroup.captcha)


if __name__ == "__main__":
    executor.start_polling(udp)

