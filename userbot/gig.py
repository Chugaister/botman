from aiogram import Bot
from aiogram.utils.exceptions import MessageCantBeDeleted, BotBlocked
from asyncio import sleep
from datetime import datetime
from pytz import timezone
from copy import copy

from data import models
from data.factory import *
from .keyboards import gen_custom_buttons
from .utils import gen_dynamic_text


mails_stats_buffer = []
purges_stats_buffer = []


async def send_mail(ubot: Bot, mail: models.Mail, admin_id: int):
    users = await user_db.get_by(bot=mail.bot)
    sent_num = 0
    blocked_num = 0
    error_num = 0
    for user in users:
        await sleep(0.035)
        mail_copy = copy(mail)
        if mail_copy.text:
            mail_copy.text = gen_dynamic_text(mail_copy.text, user)
        try:
            if mail_copy.photo:
                file = await file_manager.get_file(mail_copy.photo)
                msg = await ubot.send_photo(
                    user.id,
                    file,
                    caption=mail_copy.text,
                    reply_markup=gen_custom_buttons(mail_copy.buttons)
                )
            elif mail_copy.video:
                file = await file_manager.get_file(mail_copy.video)
                msg = await ubot.send_video(
                    user.id,
                    file,
                    caption=mail_copy.text,
                    reply_markup=gen_custom_buttons(mail_copy.buttons)
                )
            elif mail_copy.gif:
                file = await file_manager.get_file(mail_copy.gif)
                msg = await ubot.send_animation(
                    user.id,
                    file,
                    caption=mail_copy.text,
                    reply_markup=gen_custom_buttons(mail_copy.buttons)
                )
            elif mail_copy.text:
                msg = await ubot.send_message(
                    user.id,
                    mail_copy.text,
                    reply_markup=gen_custom_buttons(mail_copy.buttons)
                )
            msg_dc = models.Msg(
                msg.message_id,
                user.id,
                mail_copy.bot,
                mail_copy.del_dt.strftime(models.DT_FORMAT) if mail_copy.del_dt != None else None
            )
            await msgs_db.add(msg_dc)
            sent_num += 1
        except BotBlocked:
            user.status = 0
            await user_db.update(user)
            blocked_num += 1
        except:
            error_num += 1
    mails_stats_buffer.append({
        "admin_id": admin_id,
        "mail_id": mail.id,
        "sent_num": sent_num,
        "blocked_num": blocked_num,
        "error_num": error_num
    })
    await mails_db.delete(mail.id)


async def clean(ubot: Bot, purge: models.Purge, admin_id: int):
    msgs = await msgs_db.get_by(bot=purge.bot)
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
        await msgs_db.delete(msg.id)
    purges_stats_buffer.append({
        "admin_id": admin_id,
        "purge_id": purge.id,
        "cleared_num": cleared_num,
        "error_num": error_num
    })

