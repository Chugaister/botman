from os import path

from aiogram import Bot
from aiogram.utils.exceptions import MessageCantBeDeleted, BotBlocked, RetryAfter, UserDeactivated
from asyncio import sleep, create_task, gather, Semaphore
from datetime import datetime
from pytz import timezone
from copy import copy
from logging import getLogger
from time import time, strftime, gmtime

from data import models
from data.factory import *
from .keyboards import gen_custom_buttons
from .utils import gen_dynamic_text

mails_stats_buffer = []
admin_mails_stats_buffer = []
purges_stats_buffer = []

logger = getLogger("aiogram")
semaphore = Semaphore(3000)

async def enqueue_mail(mail: models.Mail):
    users = await user_db.get_by(bot=mail.bot, status=1)
    for user in users:
        new_mail_msgs = models.MailsQueue(
            _id=0,
            bot=mail.bot,
            user=user.id,
            mail_id=mail.id
        )
        await mails_queue_db.add(new_mail_msgs)
    mail.active = 1
    await mails_db.update(mail)


async def send_mail_to_user(ubot: Bot, mail_msg: models.MailsQueue, mail: models.Mail):
    async def kill_user(user_id):
        user_to_kill = await user_db.get(user_id)
        user_to_kill.status = 0
        await user_db.update(user_to_kill)
        mail.blocked_num += 1
        await mails_db.update(mail)

    async def del_user(user_id):
        await user_db.delete(user_id)
        mail.blocked_num += 1
        await mails_db.update(mail)

    try:
        async with semaphore:
            if mail.photo:
                msg = await ubot.send_photo(
                    mail_msg.user,
                    mail.file_id,
                    caption=gen_dynamic_text(mail.text, (await user_db.get(mail_msg.user))) if mail.text else None,
                    reply_markup=gen_custom_buttons(mail.buttons)
                )
            elif mail.video:
                msg = await ubot.send_video(
                    mail_msg.user,
                    mail.file_id,
                    caption=gen_dynamic_text(mail.text, (await user_db.get(mail_msg.user))) if mail.text else None,
                    reply_markup=gen_custom_buttons(mail.buttons)
                )
            elif mail.gif:
                msg = await ubot.send_animation(
                    mail_msg.user,
                    mail.file_id,
                    caption=gen_dynamic_text(mail.text, (await user_db.get(mail_msg.user))) if mail.text else None,
                    reply_markup=gen_custom_buttons(mail.buttons)
                )
            elif mail.text:
                msg = await ubot.send_message(
                    mail_msg.user,
                    gen_dynamic_text(mail.text, (await user_db.get(mail_msg.user))) if mail.text else None,
                    reply_markup=gen_custom_buttons(mail.buttons)
                )
            msg_dc = models.Msg(
                msg.message_id,
                mail_msg.user,
                mail.bot,
                mail.del_dt.strftime(models.DT_FORMAT) if mail.del_dt is not None else None
            )
            await msgs_db.add(msg_dc)
            mail.sent_num += 1
            await mails_db.update(mail)
    except BotBlocked:
        await kill_user(mail_msg.user)
    except UserDeactivated:
        await del_user(mail_msg.user)
    except RetryAfter as e:
        retry_after_seconds = e.timeout
        await sleep(retry_after_seconds)
        await send_mail_to_user(ubot, mail_msg, mail)
    except Exception as e:
        logger.error(f"Exception occurred while sending out mail {mail.id}: {e}", exc_info=True)
        mail.error_num += 1
        await mails_db.update(mail)
    await mails_queue_db.delete(mail_msg.id)


async def send_mail(ubot: Bot, mail: models.Mail, admin_id: int):
    start_time = time()
    mails_pending = await mails_queue_db.get_by(mail_id=mail.id, admin_status=0)
    bunches_of_tasks = []
    bunch_of_tasks = []
    for mail_msg in mails_pending:
        bunch_of_tasks.append(send_mail_to_user(ubot, mail_msg, mail))
        if len(bunch_of_tasks) >= 30:
            bunches_of_tasks.append(bunch_of_tasks)
            bunch_of_tasks = []
    if bunch_of_tasks:
        bunches_of_tasks.append(bunch_of_tasks)
    for tasks in bunches_of_tasks:
        elapsed_time = time()
        await gather(*tasks)
        await sleep(1 - time() + elapsed_time)
    end_time = time()
    elapsed_time = end_time - start_time
    formatted_time = strftime("%H:%M:%S", gmtime(elapsed_time))
    await sleep(2)

    new_action_bot = await bots_db.get(ubot.id)
    new_action_bot.action = None
    await bots_db.update(new_action_bot)
    mails_stats_buffer.append({
        "admin_id": admin_id,
        "mail_id": mail.id,
        "sent_num": mail.sent_num,
        "blocked_num": mail.blocked_num,
        "error_num": mail.error_num,
        "elapsed_time": formatted_time
    })
    mail.status = 1
    mail.active = 0
    await mails_db.update(mail)


async def clean(ubot: Bot, purge: models.Purge, admin_id: int):
    purge.active = 1
    await purges_db.update(purge)
    msgs = await msgs_db.get_by(bot=purge.bot)
    cleared_num = 0
    error_num = 0
    for msg in msgs:
        try:
            await ubot.delete_message(
                msg.user,
                msg.id
            )
            cleared_num += 1
        except Exception:
            error_num += 1
        await sleep(0.035)
    for msg in msgs:
        await msgs_db.delete(msg.id)
    purges_stats_buffer.append({
        "admin_id": admin_id,
        "purge_id": purge.id,
        "cleared_num": cleared_num,
        "error_num": error_num
    })
    await purges_db.delete(purge.id)
