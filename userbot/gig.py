from aiogram import Bot
from aiogram.utils.exceptions import MessageCantBeDeleted, BotBlocked, RetryAfter
from asyncio import sleep, create_task, Semaphore
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

# #set rate delay
# RATE_LIMIT_DELAY = 0.04
# #set first time last request time
# last_request_time = time()



async def send_mail_to_user(ubot: Bot, mail_msg: models.MailsQueue, mail: models.Mail, semaphore):
    # global last_request_time
    async with semaphore:
        try:
            #check if time between requests is bigger than  RATE_LIMIT_DELAY
            # elapsed_time = time() - last_request_time
            # if elapsed_time < RATE_LIMIT_DELAY:
            #     await asyncio.sleep(RATE_LIMIT_DELAY - elapsed_time)

            if mail.photo:
                file = await file_manager.get_file(mail.photo)
                msg = await ubot.send_photo(
                    mail_msg.user,
                    file,
                    caption=gen_dynamic_text(mail.text, (await user_db.get(mail_msg.user))) if mail.text else None,
                    reply_markup=gen_custom_buttons(mail.buttons)
                )
            elif mail.video:
                file = await file_manager.get_file(mail.video)
                msg = await ubot.send_video(
                    mail_msg.user,
                    file,
                    caption=gen_dynamic_text(mail.text, (await user_db.get(mail_msg.user))) if mail.text else None,
                    reply_markup=gen_custom_buttons(mail.buttons)
                )
            elif mail.gif:
                file = await file_manager.get_file(mail.gif)
                msg = await ubot.send_animation(
                    mail_msg.user,
                    file,
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
            last_request_time = time()
        except BotBlocked:
            user = await user_db.get(mail_msg.user)
            user.status = 0
            await user_db.update(user)
            mail.blocked_num += 1
            await mails_db.update(mail)
        except RetryAfter as e:
            retry_after_seconds = e.timeout
            await sleep(retry_after_seconds)
            await send_mail_to_user(mail_msg)
        except Exception:
            mail.error_num += 1
            await mails_db.update(mail)

        await mails_queue_db.delete(mail_msg.id)


async def send_mail(ubot: Bot, mail: models.Mail, admin_id: int):
    mails_pending = await mails_queue_db.get_by(mail_id=mail.id, admin_status=0)
    semaphore = Semaphore(30)
    tasks = [send_mail_to_user(ubot, mail_msg, mail, semaphore) for mail_msg in mails_pending]
    await asyncio.gather(*tasks)

    await sleep(3)

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
    mail.status = 1
    mail.active = 0
    await mails_db.update(mail)


async def send_admin_mail(bots: list, admin_mail: models.AdminMail, admin_id: int):
    for ubot in bots:
        active_bot_status = True
        while active_bot_status:
            bot_in_action = await bots_db.get(ubot.id)
            if not bot_in_action.action:
                active_bot_status = False
                bot_in_action.action = f"admin_mail_{admin_mail.id}"
                await bots_db.update(bot_in_action)
            elif active_bot_status:
                await sleep(2)
        admin_mails_pending = await mails_queue_db.get_by(mail_id=admin_mail.id, admin_status=1, bot=bot_in_action.id)
        for admin_mail_msg in admin_mails_pending:
            admin_mail_copy = copy(admin_mail)
            if admin_mail_copy.text:
                admin_mail_copy.text = gen_dynamic_text(admin_mail_copy.text, await user_db.get(admin_mail_msg.user))
            try:
                if admin_mail_copy.photo:
                    msg = await ubot.send_photo(
                        admin_mail_msg.user,
                        await file_manager.get_file(admin_mail_copy.photo),
                        caption=admin_mail_copy.text,
                        reply_markup=gen_custom_buttons(admin_mail_copy.buttons)
                    )
                elif admin_mail_copy.video:
                    msg = await ubot.send_video(
                        admin_mail_msg.user,
                        await file_manager.get_file(admin_mail_copy.video),
                        caption=admin_mail_copy.text,
                        reply_markup=gen_custom_buttons(admin_mail_copy.buttons)
                    )
                elif admin_mail_copy.gif:
                    msg = await ubot.send_animation(
                        admin_mail_msg.user,
                        file_manager.get_file(admin_mail_copy.gif),
                        caption=admin_mail_copy.text,
                        reply_markup=gen_custom_buttons(admin_mail_copy.buttons)
                    )
                elif admin_mail_copy.text:
                    msg = await ubot.send_message(
                        admin_mail_msg.user,
                        admin_mail_copy.text,
                        reply_markup=gen_custom_buttons(admin_mail_copy.buttons)
                    )
                msg_dc = models.Msg(
                    msg.message_id,
                    admin_mail_msg.user,
                    ubot.id,
                    None
                )
                await msgs_db.add(msg_dc)
                admin_mail.sent_num += 1
                await admin_mails_db.update(admin_mail)
            except BotBlocked:
                user = await user_db.get(admin_mail_msg.user)
                user.status = 0
                await user_db.update(user)
                admin_mail.blocked_num += 1
                await admin_mails_db.update(admin_mail)
            except Exception:
                admin_mail.error_num += 1
                await admin_mails_db.update(admin_mail)
            await mails_queue_db.delete(admin_mail_msg.id)
            if not (await mails_queue_db.get_by(bot=ubot.id, admin_status=True)):
                new_action_bot = await bots_db.get(ubot.id)
                new_action_bot.action = None
                await bots_db.update(new_action_bot)
            await sleep(0.035)
    admin_mails_stats_buffer.append({
        "admin_id": admin_id,
        "mail_id": admin_mail.id,
        "sent_num": admin_mail.sent_num,
        "blocked_num": admin_mail.blocked_num,
        "error_num": admin_mail.error_num
    })
    admin_mail.status = 1
    admin_mail.active = 0
    await admin_mails_db.update(admin_mail)


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
