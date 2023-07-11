from aiogram import Bot
from aiogram.utils.exceptions import MessageCantBeDeleted, BotBlocked
from asyncio import sleep
from datetime import datetime
from pytz import timezone
from copy import copy
from time import time

from data import models
from data.factory import *
from .keyboards import gen_custom_buttons
from .utils import gen_dynamic_text

mails_stats_buffer = []
admin_mails_stats_buffer = []
purges_stats_buffer = []

mails_stats_buffer = []
purges_stats_buffer = []


async def send_mail(ubot: Bot, mail: models.Mail, admin_id: int):
    mail.active = 1
    await mails_db.update(mail)
    users = await user_db.get_by(bot=mail.bot)
    sent_num = 0
    blocked_num = 0
    error_num = 0
    if mail.photo:
        file = await file_manager.get_file(mail.photo)
    elif mail.video:
        file = await file_manager.get_file(mail.video)
    elif mail.gif:
        file = await file_manager.get_file(mail.gif)
    for user in users:
        await sleep(0.035)
        mail_copy = copy(mail)
        if mail_copy.text:
            mail_copy.text = gen_dynamic_text(mail_copy.text, user)
        try:
            if mail_copy.photo:
                file = await file_manager.get_file(mail.photo)
                msg = await ubot.send_photo(
                    user.id,
                    file,
                    caption=mail_copy.text,
                    reply_markup=gen_custom_buttons(mail_copy.buttons)
                )
            elif mail_copy.video:
                file = await file_manager.get_file(mail.video)
                msg = await ubot.send_video(
                    user.id,
                    file,
                    caption=mail_copy.text,
                    reply_markup=gen_custom_buttons(mail_copy.buttons)
                )
            elif mail_copy.gif:
                file = await file_manager.get_file(mail.gif)
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


async def send_admin_mail(bots: list, admin_mail: models.AdminMail, admin_id: int):
    admin_mail.active = 1
    await admin_mails_db.update(admin_mail)
    sent_num = 0
    blocked_num = 0
    error_num = 0
    for ubot in bots:
        users = await user_db.get_by(bot=ubot.id)
        for user in users:
            await sleep(0.035)
            if admin_mail.text:
                admin_mail.text = gen_dynamic_text(admin_mail.text, user)
            try:
                if admin_mail.photo:
                    msg = await ubot.send_photo(
                        user.id,
                        await file_manager.get_file(admin_mail.photo),
                        caption=admin_mail.text,
                        reply_markup=gen_custom_buttons(admin_mail.buttons)
                    )
                elif admin_mail.video:
                    msg = await ubot.send_video(
                        user.id,
                        await file_manager.get_file(admin_mail.video),
                        caption=admin_mail.text,
                        reply_markup=gen_custom_buttons(admin_mail.buttons)
                    )
                elif admin_mail.gif:
                    msg = await ubot.send_animation(
                        user.id,
                        file_manager.get_file(admin_mail.gif),
                        caption=admin_mail.text,
                        reply_markup=gen_custom_buttons(admin_mail.buttons)
                    )
                elif admin_mail.text:
                    msg = await ubot.send_message(
                        user.id,
                        admin_mail.text,
                        reply_markup=gen_custom_buttons(admin_mail.buttons)
                    )
                msg_dc = models.Msg(
                    msg.message_id,
                    user.id,
                    ubot.id,
                    None
                )
                await msgs_db.add(msg_dc)
                sent_num += 1
            except BotBlocked:
                user.status = 0
                await user_db.update(user)
                blocked_num += 1
            except:
                error_num += 1
    admin_mails_stats_buffer.append({
        "admin_id": admin_id,
        "mail_id": admin_mail.id,
        "sent_num": sent_num,
        "blocked_num": blocked_num,
        "error_num": error_num
    })
    await admin_mails_db.delete(admin_mail.id)


async def clean(ubot: Bot, purge: models.Purge, admin_id: int):
    purge.active = 1
    await purges_db.update(purge)
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
    await purges_db.delete(purge.id)

