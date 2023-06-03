from aiogram import Bot
from aiogram.utils.exceptions import MessageCantBeDeleted
from asyncio import sleep
from datetime import datetime
from pytz import timezone

from data import models
from data.factory import *
from .keyboards import gen_custom_buttons


async def send_mail(ubot: Bot, mail: models.Mail):
    users = user_db.get_by(bot=mail.bot)
    mails_db.delete(mail.id)
    for user in users:
        await sleep(0.035)
        if mail.photo:
            file = await file_manager.get_file(mail.photo)
            msg = await ubot.send_photo(
                user.id,
                file,
                caption=mail.text,
                reply_markup=gen_custom_buttons(mail.buttons)
            )
        elif mail.video:
            file = await file_manager.get_file(mail.video)
            msg = await ubot.send_video(
                user.id,
                file,
                caption=mail.text,
                reply_markup=gen_custom_buttons(mail.buttons)
            )
        elif mail.gif:
            file = await file_manager.get_file(mail.gif)
            msg = await ubot.send_animation(
                user.id,
                file,
                caption=mail.text,
                reply_markup=gen_custom_buttons(mail.buttons)
            )
        elif mail.text:
            msg = await ubot.send_message(
                user.id,
                mail.text,
                reply_markup=gen_custom_buttons(mail.buttons)
            )
        msg_dc = models.Msg(
            msg.message_id,
            user.id,
            mail.bot,
            mail.del_dt
        )
        msgs_db.add(msg_dc)


async def clean(ubot: Bot, purge: models.Purge):
    msgs = msgs_db.get_by(bot=purge.bot)
    purges_db.delete(purge.id)
    for msg in msgs:
        await sleep(0.035)
        await ubot.delete_message(
            msg.user,
            msg.id
        )
    for msg in msgs:
        msgs_db.delete(msg.id)

