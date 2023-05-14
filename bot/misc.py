from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, ChatJoinRequest, ContentTypes, ParseMode
from aiogram.dispatcher.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import MessageCantBeDeleted, MessageNotModified
from aiogram.utils.callback_data import CallbackData

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from pytz import timezone
from datetime import datetime
from asyncio import sleep
import logging
from requests import get
from prettytable import PrettyTable

from data import models
from data.stats import gen_stats
from data.database import Database, get_db
from data import exceptions as data_exc

from . import config, states
ukraine_tz = timezone('Europe/Kiev')
logging.basicConfig(level=logging.INFO)
bot = Bot(config.token, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

db_conn = get_db("source")

admins_db = Database("admins", db_conn, models.Admin)
bots_db = Database("bots", db_conn, models.Bot)
user_db = Database("users", db_conn, models.User)
captchas_db = Database("captchas", db_conn, models.Captcha)
greeting_db = Database("greetings", db_conn, models.Greeting)
mails_db = Database("mails", db_conn, models.Mail)
purges_db = Database("purges", db_conn, models.Purge)
msgs_db = Database("msgs", db_conn, models.Msg)



