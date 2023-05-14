from aiogram import executor
from bot.misc import dp
import bot.handlers


if __name__ == "__main__":
    executor.start_polling(dp)
