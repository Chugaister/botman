from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, ChatJoinRequest, ContentTypes, ParseMode
from aiogram.dispatcher.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import MessageCantBeDeleted, MessageNotModified, MessageToDeleteNotFound, ChatNotFound
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

from configs import args_parse,  config
# try:
#     from . import config
# except ImportError:
#     print("config.py not found")
#     exit()


tz = timezone('Europe/Kiev')
# parser = argparse.ArgumentParser()
# parser.add_argument('--local', action='store_true', help='Run in local mode')
# parser.add_argument('--token', action='store', help='Bot token to run on')
# parser.add_argument('--port', action='store', help='Select the port to run on')
# parser.add_argument('--source', action='store', help='Database folder path')
# parser.add_argument('--logs', action='store', help='Logs folder path')
# args = parser.parse_args()

args = args_parse.args

if args.token:
    bot = Bot(args.token, parse_mode='HTML')
else:
    print("misc print: ", config.token)
    token = config.token
    bot = Bot(token, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


if args.local:
    from configs import local_config
    WEBHOOK_HOST = local_config.WEBHOOK_HOST 
    # from web_config.local_config import WEBHOOK_HOST
    manager = Manager([], WEBHOOK_HOST)
    manager.updates[config.token] = 0
else:
    from configs import config
    WEBHOOK_HOST = config.WEBHOOK_HOST
    # from web_config.config import WEBHOOK_HOST
    manager = Manager([], WEBHOOK_HOST)
    manager.updates[config.token] = 0
    
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
