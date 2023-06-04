from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, ChatJoinRequest, ContentTypes, ParseMode
from aiogram.dispatcher.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import MessageCantBeDeleted, MessageNotModified, MessageToDeleteNotFound
from aiogram.utils.callback_data import CallbackData

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from pytz import timezone
from datetime import datetime
from asyncio import sleep, get_event_loop
import logging
from requests import get
from prettytable import PrettyTable
from os import path
from sys import exit

from data import exceptions as data_exc
from data.stats import gen_stats
from data.factory import *
from userbot import gig

from . import states
import asyncio
from manager.manager import Manager

try:
    from . import config
except ImportError:
    print("config.py not found")
    exit()


ukraine_tz = timezone('Europe/Kiev')
logging.basicConfig(level=logging.INFO)
bot = Bot(config.token, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

manager = Manager([])
# get_event_loop().run_until_complete(manager.set_webhook(ubots))
