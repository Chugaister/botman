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


async def send_mail(ubot: Bot, mail: models.Mail, admin_id: int):
    mails_pending = mails_queue_db.get_by(mail_id=mail, admin_status=0)
    for mail_msg in mails_pending:
        await sleep(0.3)
        mail_copy = copy(mail)
        if mail_copy.text:
            mail_copy.text = gen_dynamic_text(mail_copy.text, user_db.get(mail_msg.user))
        try:
            if mail_copy.photo:
                file = await file_manager.get_file(mail.photo)
                msg = await ubot.send_photo(
                    mail_msg.user,
                    file,
                    caption=mail_copy.text,
                    reply_markup=gen_custom_buttons(mail_copy.buttons)
                )
            elif mail_copy.video:
                file = await file_manager.get_file(mail.video)
                msg = await ubot.send_video(
                    mail_msg.user,
                    file,
                    caption=mail_copy.text,
                    reply_markup=gen_custom_buttons(mail_copy.buttons)
                )
            elif mail_copy.gif:
                file = await file_manager.get_file(mail.gif)
                msg = await ubot.send_animation(
                    mail_msg.user,
                    file,
                    caption=mail_copy.text,
                    reply_markup=gen_custom_buttons(mail_copy.buttons)
                )
            elif mail_copy.text:
                msg = await ubot.send_message(
                    mail_msg.user,
                    mail_copy.text,
                    reply_markup=gen_custom_buttons(mail_copy.buttons)
                )
            msg_dc = models.Msg(
                msg.message_id,
                mail_msg.user,
                mail_copy.bot,
                mail_copy.del_dt.strftime(models.DT_FORMAT) if mail_copy.del_dt is not None else None
            )
            await msgs_db.add(msg_dc)
            mail.sent_num += 1
            mails_db.update(mail)
        except BotBlocked:
            user = user_db.get(mail_msg.user)
            user.status = 0
            await user_db.update(user)
            mail.blocked_num += 1
        except:
            mail.error_num += 1
        await mails_queue_db.delete(mail_msg)
    new_action_bot = await bots_db.get(ubot.id)
    new_action_bot.action = None
    await bots_db.update(new_action_bot)
    mails_stats_buffer.append({
        "admin_id": admin_id,
        "mail_id": mail.id,
        "sent_num": mail.sent_num,
        "blocked_num": mail.blocked_num,
        "error_num": mail.error_num
    })
    await mails_db.delete(mail)


# async def send_admin_mail(bots: list, admin_mail: models.AdminMail, admin_id: int):
#     admin_mails_pending = await mails_queue_db.get_by(mail_id=admin_mail.id, admin_status=1)
#     for admin_mail_msg in admin_mails_pending:
#         await sleep(0.035)
#         admin_mail_copy = copy(admin_mail)
#         if admin_mail_copy.text:
#             admin_mail_copy.text = gen_dynamic_text(admin_mail_copy.text, user_db.get(admin_mail_msg.user))
#         for bot_dc in bots:
#             if bot_dc.token == await bot_dc.
#         try:
#             if admin_mail_copy.photo:
#                 msg = await ubot.send_photo(
#                     mails_queue_db.user,
#                     await file_manager.get_file(admin_mail_copy.photo),
#                     caption=admin_mail_copy.text,
#                     reply_markup=gen_custom_buttons(admin_mail_copy.buttons)
#                 )
#             elif admin_mail_copy.video:
#                 msg = await ubot.send_video(
#                     mails_queue_db.user,
#                     await file_manager.get_file(admin_mail_copy.video),
#                     caption=admin_mail_copy.text,
#                     reply_markup=gen_custom_buttons(admin_mail_copy.buttons)
#                 )
#             elif admin_mail_copy.gif:
#                 msg = await ubot.send_animation(
#                     mails_queue_db.user,
#                     file_manager.get_file(admin_mail_copy.gif),
#                     caption=admin_mail_copy.text,
#                     reply_markup=gen_custom_buttons(admin_mail_copy.buttons)
#                 )
#             elif admin_mail_copy.text:
#                 msg = await ubot.send_message(
#                     mails_queue_db.user,
#                     admin_mail_copy.text,
#                     reply_markup=gen_custom_buttons(admin_mail_copy.buttons)
#                 )
#             msg_dc = models.Msg(
#                 msg.message_id,
#                 admin_mail_msg.user,
#                 ubot.id,
#                 None
#             )
#             await msgs_db.add(msg_dc)
#             admin_mail.sent_num += 1
#             await admin_mails_db.update(admin_mail)
#         except BotBlocked:
#             user = user_db.get(admin_mail_msg.user)
#             user.status = 0
#             await user_db.update(user)
#             admin_mail.blocked_num += 1
#             await admin_mails_db.update(admin_mail)
#         except:
#             admin_mail.error_num += 1
#             await admin_mails_db.update(admin_mail)
#         await mails_queue_db.delete(admin_mail_msg)
#         if not (await mails_queue_db.get_by(bot=ubot.id)):
#             new_action_bot = await bots_db.get(ubot.id)
#             new_action_bot.action = None
#             await bots_db.update(new_action_bot)
#     admin_mails_stats_buffer.append({
#         "admin_id": admin_id,
#         "mail_id": admin_mail.id,
#         "sent_num": admin_mail.sent_num,
#         "blocked_num": admin_mail.blocked_num,
#         "error_num": admin_mail.error_num
#     })
#     await admin_mails_db.delete(admin_mail.id)


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
