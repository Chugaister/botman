from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, ChatJoinRequest, ContentTypes, ParseMode
from aiogram.dispatcher.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import MessageCantBeDeleted, MessageNotModified, MessageToDeleteNotFound
from aiogram.utils.callback_data import CallbackData
import re
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from pytz import timezone
from datetime import datetime
from asyncio import sleep, get_event_loop, create_task
import logging
from requests import get
from prettytable import PrettyTable
from os import path
from sys import exit
import argparse
from data import exceptions as data_exc
from data.stats import gen_stats
from data.factory import *
from userbot import gig
import sys

from . import states
import asyncio
from manager.manager import Manager

try:
    from . import config
except ImportError:
    print("config.py not found")
    exit()


tz = timezone('Europe/Kiev')
parser = argparse.ArgumentParser()
parser.add_argument('--local', action='store_true', help='Run in local mode')
parser.add_argument('--token', action='store', help='Bot token to run on')
parser.add_argument('--port', action='store', help='Select the port to run on')
parser.add_argument('--source', action='store', help='Database folder path')
args = parser.parse_args()

if args.token:
    bot = Bot(args.token, parse_mode='HTML')
else:
    bot = Bot(config.token, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


if args.local:
    from web_config.local_config import WEBHOOK_HOST
    manager = Manager([], WEBHOOK_HOST)
else:
    from web_config.config import WEBHOOK_HOST
    manager = Manager([], WEBHOOK_HOST)
    
# get_event_loop().run_until_complete(manager.set_webhook(ubots))


async def safe_del_msg(uid: int, msg_id: int):
    try:
        await bot.delete_message(
            uid,
            msg_id
        )
    except MessageCantBeDeleted:
        pass
    except MessageToDeleteNotFound:
        pass


async def safe_edit_message(text: str, chat_id: int, message_id: int, reply_markup):
    try:
        await bot.edit_message_text(
            text,
            chat_id,
            message_id,
            reply_markup=reply_markup
        )
    except MessageNotModified:
        pass


def gen_hex_caption(id: int) -> str:
    return str(hex(id*1234))
