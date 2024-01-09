from bot.misc import *
from bot.keyboards import gen_ok
from bot.handlers import admin_notification
from bot.handlers.multi_mails import run_multi_mail
from logging import getLogger
import subprocess
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

logger = getLogger("aiogram")


def count_output_lines(command):
    try:
        # Run the system command and capture its output
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Check if the command was successful
        if result.returncode == 0:
            # Split the output into lines and count the number of lines
            output_lines = result.stdout.splitlines()
            num_lines = len(output_lines)
            return num_lines
        else:
            return None
    except Exception as e:
        return None


# start_action() check if action can be done(after enqueue) and update status in db of action
# gets: action - from models(models.Purge or models.Mail)
#       bot_dc - bot from Database class(models.Bot)
#       db_of_action - Database class of this action
#       action_type - string which contains name of action
# returns: True or False
async def start_action(action, bot_dc: models.Bot, db_of_action, action_type: str):
    # check if action is enqueued and bot is idle
    if not bot_dc.action and action.active and not action.status:

        # set status to started
        action.status = 1
        await db_of_action.update(action)

        # set action to the bot(set that bot is busy)
        bot_dc.action = f"{action_type}_{action.id}"
        await bots_db.update(bot_dc)

        return True
    else:
        return False


# queue_action() check if we can enqueue action and do it
# gets: action - from models(models.Purge or models.Mail)
#       db_of_action - Database class of this action
#       action_type - string which contains name of action
# returns: True or False
async def queue_action(action, db_of_action, action_type: str):
    # set condition for diff types to check if action should queue
    condition = False
    if isinstance(action, models.Purge):
        condition = action.sched_dt and datetime.now(tz=tz) > tz.localize(
            action.sched_dt) and not action.active and not action.status
    elif isinstance(action, models.Mail) or isinstance(action, models.MultiMail):
        condition = action.send_dt and datetime.now(tz=tz) > tz.localize(
            action.send_dt) and not action.active and not action.status

    # check this condition
    if condition:

        # if action is mail, enqueue mail and add purge if that mail have auto-deleting
        if action_type == "mail":
            await gig.enqueue_mail(action)
            if action.del_dt:
                purge = models.Purge(0, sender=action.sender, bot=action.bot,
                                     sched_dt=datetime.strftime(action.del_dt, models.DT_FORMAT),
                                     mail_id=action.id)
                await purges_db.add(purge)

        # update status of action to enqueued
        action.active = 1
        await db_of_action.update(action)

        return True
    else:
        return False


# listen_purges() is listener which check all purges for start
# gets: nothing
# returns: nothing
async def listen_purges():
    # get all purges, which don't started and don't enqueued from db and start checking for each
    purges = await purges_db.get_by(active=0, status=0)
    for purge in purges:

        # get bot data from db
        bot_dc = await bots_db.get(purge.bot)

        # check if purge is cleaning of bot or is auto-deleting of mail and set msg text
        if purge.mail_id:
            mail = await mails_db.get(purge.mail_id)
            if mail.multi_mail:
                queue_msg = f"🕑Видалення({gen_hex_caption(purge.id)}) мультирозсилки {gen_hex_caption(mail.multi_mail)} у боті @{bot_dc.username} було поставлено в чергу. Вам прийде повідомлення коли воно розпочнеться"
            else:
                queue_msg = f"🕑Видалення({gen_hex_caption(purge.id)}) розсилки {gen_hex_caption(purge.mail_id)} у боті @{bot_dc.username} було поставлено в чергу. Вам прийде повідомлення коли воно розпочнеться"

        else:
            queue_msg = f"🕑Чистка({gen_hex_caption(purge.id)}) у боті @{bot_dc.username} була поставлена в чергу. Вам прийде повідомлення коли вона розпочнеться"

        # if purge is enqueued, send msg to sender of it enqueueing
        if await queue_action(purge, purges_db, "purge"):
            await bot.send_message(purge.sender, queue_msg, reply_markup=gen_ok("hide"))


async def listen_start_purges():
    # get all purges, which don't started but enqueued from db and start checking for each
    purges = await purges_db.get_by(active=1, status=0)

    # if not any purges which we need stop listeners
    if not purges:
        return

    for purge in purges:
        # get bot data from db
        bot_dc = await bots_db.get(purge.bot)

        # check if purge is cleaning of bot or is auto-deleting of mail and set msg text
        if purge.mail_id:
            mail = await mails_db.get(purge.mail_id)
            if mail.multi_mail:
                start_msg = f"♻️Видалення({gen_hex_caption(purge.id)}) мультирозсилки {gen_hex_caption(mail.multi_mail)} в боті @{bot_dc.username} розпочато. Вам прийде повідомлення після його закінчення"
            else:
                start_msg = f"♻️Видалення({gen_hex_caption(purge.id)}) розсилки {gen_hex_caption(purge.mail_id)} в боті @{bot_dc.username} розпочато. Вам прийде повідомлення після його закінчення"
        else:
            start_msg = f"♻️Чистка {gen_hex_caption(purge.id)} в боті @{bot_dc.username} розпочата. Вам прийде повідомлення після її закінчення"

        # if purge can be started, then send msg to sender of it starting and starts purge in userbot
        if await start_action(purge, bot_dc, purges_db, "purge"):
            await bot.send_message(purge.sender, start_msg, reply_markup=gen_ok("hide"))
            create_task(
                gig.clean(manager.bot_dict[(await bots_db.get_by(id=purge.bot))[0].token][0], purge, purge.sender))


# listen_mails() is listener which check all mails for start
# gets: nothing
# returns: nothing
async def listen_mails():
    # get all mails from db, which don't started and don't enqueued from db and start checking for each
    mails = await mails_db.get_by(active=0, status=0)

    # if not any purges which we need stop listeners
    if not mails:
        return

    for mail in mails:

        # get bot data from db
        bot_dc = await bots_db.get(mail.bot)

        # if mail is enqueued, send msg to sender of it enqueueing
        if await queue_action(mail, mails_db, "mail"):
            queue_msg = f"🕑Розсилка {gen_hex_caption(mail.id)} у боті @{bot_dc.username} була поставлена в чергу. Вам прийде повідомлення коли вона розпочнеться"
            await bot.send_message(mail.sender, queue_msg, reply_markup=gen_ok("hide"))


async def listen_start_mail():
    # get all mails, which don't started but enqueued from db and start checking for each
    mails = await mails_db.get_by(active=1, status=0)

    # if not any purges which we need stop listeners
    if not mails:
        return None

    for mail in mails:
        # get bot data from db
        bot_dc = await bots_db.get(mail.bot)

        # if mail can be started, then send msg to sender of it starting and starts purge in userbot
        if await start_action(mail, bot_dc, mails_db, "mail"):
            if not mail.multi_mail:
                start_msg = f"🚀Розсилка {gen_hex_caption(mail.id)} в боті @{bot_dc.username} розпочата. Вам прийде повідомлення після її закінчення"
                await bot.send_message(mail.sender, start_msg, reply_markup=gen_ok("hide"))
            create_task(gig.send_mail(manager.bot_dict[(await bots_db.get_by(id=mail.bot))[0].token][0], mail,
                                      mail.sender))


# listen_multi_mails() is listener which check all multi_mails for start
# gets: nothing
# returns: nothing
async def listen_multi_mails():
    multi_mails = await multi_mails_db.get_by(active=0, status=0)
    for multi_mail in multi_mails:
        if await queue_action(multi_mail, multi_mails_db, "multi_mail"):
            create_task(run_multi_mail(multi_mail, multi_mail.sender))


# listen_mails_stats() is listener which check buffet of mail stats and send stats to sender
# gets: nothing
# returns: nothing
async def listen_mails_stats():
    if gig.mails_stats_buffer:
        for mail_stats in gig.mails_stats_buffer:
            mail = await mails_db.get(mail_stats["mail_id"])
            if not mail.multi_mail:
                await bot.send_message(
                    mail_stats["admin_id"],
                    f"📭Розсилка {gen_hex_caption(mail_stats['mail_id'])} в боті @{(await bots_db.get(mail.bot)).username} закінчена\n\n\
✅Надіслано: {mail_stats['sent_num']}\n💀Заблоковано: {mail_stats['blocked_num']}\n❌Помилка: {mail_stats['error_num']}\n\
⌛️Час розсилання: {mail_stats['duration']}",
                    reply_markup=gen_ok("hide")
                )
        gig.mails_stats_buffer = []


# listen_multi_mail_stats() is listener which check buffet of multi_mail stats and send stats to sender
# gets: nothing
# returns: nothing
async def listen_multi_mail_stats():
    multi_mails = await multi_mails_db.get_by(active=1, status=0)
    for multi_mail in multi_mails:
        mails = await mails_db.get_by(multi_mail=multi_mail.id)
        finished = True
        for mail in mails:
            finished = finished and (not mail.active and mail.status)
        multi_mail.sent_num = int(multi_mail.sent_num)
        multi_mail.blocked_num = int(multi_mail.blocked_num)
        multi_mail.error_num = int(multi_mail.error_num)
        if finished:
            for mail in mails:
                multi_mail.sent_num += mail.sent_num
                multi_mail.blocked_num += mail.blocked_num
                multi_mail.error_num += mail.error_num
            multi_mail.active = 0
            multi_mail.status = 1
            await multi_mails_db.update(multi_mail)
            if multi_mail.admin:
                await bot.send_message(
                    multi_mail.sender,
                    f"📭Адмінська розсилка {gen_hex_caption(multi_mail.id)} закінчена\n\n✅Надіслано: {multi_mail.sent_num}\n💀Заблоковано: {multi_mail.blocked_num}\n❌Помилка: {multi_mail.error_num}",
                    reply_markup=gen_ok("hide", "Оце їбано, ну а шо ти думав, адмін?")
                )
            else:
                await bot.send_message(
                    multi_mail.sender,
                    f"📭Мультирозсилка {gen_hex_caption(multi_mail.id)} закінчена\n\n✅Надіслано: {multi_mail.sent_num}\n💀Заблоковано: {multi_mail.blocked_num}\n❌Помилка: {multi_mail.error_num}",
                    reply_markup=gen_ok("hide")
                )


# listen_admin_notification_stats() is listener which check buffet of admin notification stats and send stats to sender
# gets: nothing
# returns: nothing
async def listen_admin_notification_stats():
    if admin_notification.admin_notification_stats:
        for notification_stats in admin_notification.admin_notification_stats:
            await bot.send_message(
                notification_stats["admin_id"],
                f"📭Сповіщення адмінів закінчено\n\
Надіслано: {notification_stats['sent_num']}\nЗаблоковано: {notification_stats['blocked_num']}\nПомилка: {notification_stats['error_num']}",
                reply_markup=gen_ok("hide")
            )
        admin_notification.admin_notification_stats = []


# listen_purges_stats() is listener which check buffet of purge stats and send stats to sender
# gets: nothing
# returns: nothing
async def listen_purges_stats():
    if gig.purges_stats_buffer != []:
        for purge_stats in gig.purges_stats_buffer:
            purge = await purges_db.get(purge_stats['purge_id'])
            if purge.mail_id:
                await bot.send_message(
                    purge_stats["admin_id"],
                    f"📭Видалення {gen_hex_caption(purge_stats['purge_id'])} розсилки {gen_hex_caption(purge.mail_id)} в боті @{(await bots_db.get(purge.bot)).username} закінчено\n\n\
✅Очищено: {purge_stats['cleared_num']}\n❌Помилка: {purge_stats['error_num']}\n\
⌛️Час розсилання: {purge_stats['duration']}",
                    reply_markup=gen_ok("hide")
                )
            else:
                await bot.send_message(
                    purge_stats["admin_id"],
                    f"📭Чистка {gen_hex_caption(purge_stats['purge_id'])} в боті @{(await bots_db.get(purge.bot)).username} закінчена\n\n\
✅Очищено: {purge_stats['cleared_num']}\n❌Помилка: {purge_stats['error_num']}\n\
⌛️Час розсилання: {purge_stats['duration']}",
                    reply_markup=gen_ok("hide")
                )
        gig.purges_stats_buffer = []


# resume_action() resume all action after startup
# gets: nothing
# returns: nothing
async def resume_action():
    ubots = []
    ubots_all = await bots_db.get_all()
    for ubot in ubots_all:
        if ubot.status == 1 and ubot.admin:
            ubots.append(ubot)
    for ubot in ubots:
        if ubot.action:
            ubot_action_all = ubot.action.split("_")
            if ubot_action_all[0] == "mail":
                mail = await mails_db.get(ubot_action_all[1])
                bot_dc = manager.bot_dict[(await bots_db.get_by(id=mail.bot))[0].token][0]
                create_task(gig.send_mail(bot_dc, mail, mail.sender))
            elif ubot_action_all[0] == "purge":
                purge = await purges_db.get(ubot_action_all[1])
                bot_dc = manager.bot_dict[(await bots_db.get_by(id=purge.bot))[0].token][0]
                create_task(gig.clean(bot_dc, purge, purge.sender))


# run_listeners() run all listeners on startup
async def run_listeners():
    await resume_action()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(listen_mails_stats, 'interval', seconds=5)
    scheduler.add_job(listen_purges_stats, 'interval', seconds=5)
    scheduler.add_job(listen_admin_notification_stats, 'interval', seconds=5)
    scheduler.add_job(listen_multi_mail_stats, 'interval', seconds=5)

    scheduler.add_job(listen_mails, 'interval', seconds=15)
    scheduler.add_job(listen_start_mail, 'interval', seconds=15)

    scheduler.start()

    await sleep(5)
    scheduler.add_job(listen_purges, 'interval', seconds=15)
    scheduler.add_job(listen_start_purges, 'interval', seconds=15)

    await sleep(5)
    scheduler.add_job(listen_multi_mails, 'interval', seconds=15)

