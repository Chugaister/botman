from aiogram import Bot
from aiogram.utils.exceptions import MessageCantBeDeleted, BotBlocked
from asyncio import sleep
from datetime import datetime
from pytz import timezone

from data import models
from data.factory import *
from .keyboards import gen_custom_buttons


async def send_mail(ubot: Bot, mail: models.Mail):
    users = user_db.get_by(bot=mail.bot)
    sent_num = 0
    blocked_num = 0
    error_num = 0
    for user in users:
        await sleep(0.035)
        try:
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
                mail.del_dt.strftime(models.DT_FORMAT)
            )
            msgs_db.add(msg_dc)
            sent_num += 1
        except BotBlocked:
            blocked_num += 1
        except:
            error_num += 1
    return sent_num, blocked_num, error_num


async def clean(ubot: Bot, purge: models.Purge):
    msgs = msgs_db.get_by(bot=purge.bot)
    cleared_num = 0
    error_num = 0
    for msg in msgs:
        await sleep(0.035)
        try:
            await ubot.delete_message(
                msg.user,
                msg.id
            )
            cleared_num += 1
        except:
            error_num += 1
    for msg in msgs:
        msgs_db.delete(msg.id)
    return cleared_num, error_num

