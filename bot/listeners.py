from bot.misc import *
from bot.keyboards import gen_ok
from bot.handlers import admin_notification

from logging import getLogger
import subprocess
import os

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


async def start_action_check(action, bot_dc: models.Bot):
    if isinstance(action, models.Purge):
        db_of_action = purges_db
        action_type = "purge"
        if action.mail_id:
            start_msg = f"🚀Видалення({gen_hex_caption(action.id)}) розсилки {gen_hex_caption(action.mail_id)} в боті @{bot_dc.username} було розпочато. Вам прийде повідомлення після його закінчення"
        else:
            start_msg = f"🚀Чистка {gen_hex_caption(action.id)} в боті @{bot_dc.username} розпочата. Вам прийде повідомлення після її закінчення"
    elif isinstance(action, models.Mail):
        db_of_action = mails_db
        action_type = "mail"
        start_msg = f"🚀Розсилка {gen_hex_caption(action.id)} в боті @{bot_dc.username} розпочата. Вам прийде повідомлення після її закінчення"
    else:
        return TypeError

    if not bot_dc.action and action.active and not action.status:
        await bot.send_message(action.sender, start_msg, reply_markup=gen_ok("hide"))
        action.status = 1
        await db_of_action.update(action)
        bot_dc.action = f"{action_type}_{action.id}"
        await bots_db.update(bot_dc)
        return True
    else:
        return False


async def check_start_action_time(action, bot_dc: models.Bot):
    if isinstance(action, models.Purge):
        condition = action.sched_dt and datetime.now(tz=tz) > tz.localize(
            action.sched_dt) and not action.active and not action.status
        db_of_action = purges_db
        action_type = "purge"
        if action.mail_id:
            queue_msg = f"Видалення({gen_hex_caption(action.id)}) розсилки {gen_hex_caption(action.mail_id)} у боті @{bot_dc.username} було поставлено в чергу. Вам прийде повідомлення коли воно розпочнеться"
        else:
            queue_msg = f"Чистка({gen_hex_caption(action.id)}) у боті @{bot_dc.username} була поставлена в чергу. Вам прийде повідомлення коли вона розпочнеться"
    elif isinstance(action, models.Mail):
        condition = action.send_dt and datetime.now(tz=tz) > tz.localize(
            action.send_dt) and not action.active and not action.status
        db_of_action = mails_db
        action_type = "mail"
        queue_msg = f"Розсилка {gen_hex_caption(action.id)} у боті @{bot_dc.username} була поставлена в чергу. Вам прийде повідомлення коли вона розпочнеться"
    else:
        return TypeError

    if condition:
        if action_type == "mail":
            await gig.enqueue_mail(action)
        action.active = 1
        await db_of_action.update(action)
        await bot.send_message(action.sender, queue_msg, reply_markup=gen_ok("hide"))


async def listen_purges():
    while True:
        purges = await purges_db.get_all()
        for purge in purges:
            bot_dc = await bots_db.get(purge.bot)
            await check_start_action_time(purge, bot_dc)
            if await start_action_check(purge, bot_dc):
                create_task(
                    gig.clean(manager.bot_dict[(await bots_db.get_by(id=purge.bot))[0].token][0], purge, purge.sender))
        await sleep(5)


async def listen_mails():
    while True:
        cmd = f"sudo lsof -p {os.getpid()}"
        logger.debug(f"Number of open files: {count_output_lines(cmd)}")
        try:
            mails = await mails_db.get_all()
        except ValueError:
            print("ERROR: mail buttons deserialization failed")
            await sleep(5)
            continue
        for mail in mails:
            bot_dc = await bots_db.get(mail.bot)
            await check_start_action_time(mail, bot_dc)
            if await start_action_check(mail, bot_dc):
                if mail.del_dt:
                    purge = models.Purge(0, bot=mail.bot, sched_dt=datetime.strftime(mail.del_dt, models.DT_FORMAT),
                                         mail_id=mail.id, sender=mail.sender)
                    await purges_db.add(purge)
                create_task(gig.send_mail(manager.bot_dict[(await bots_db.get_by(id=mail.bot))[0].token][0], mail,
                                          mail.sender))
        await sleep(5)


async def listen_admin_mails():
    while True:
        admin_mails = await admin_mails_db.get_all()
        for admin_mail in admin_mails:
            if admin_mail.send_dt and datetime.now(tz=timezone('Europe/Kiev')) > tz.localize(
                    admin_mail.send_dt) and not admin_mail.active and not admin_mail.status:
                bots = [ubot for ubot in await bots_db.get_by(premium=0)]
                for ubot in bots:
                    users = await user_db.get_by(bot=ubot.id)
                    for user in users:
                        new_mail_msgs = models.MailsQueue(
                            _id=0,
                            bot=admin_mail.bot,
                            user=user.id,
                            mail_id=admin_mail.id,
                            admin_status=True
                        )
                        await mails_queue_db.add(new_mail_msgs)
                    admin_mail.active = 1
                    await mails_db.update(admin_mail)

            if admin_mail.active and not admin_mail.status:
                await bot.send_message(
                    admin_mail.sender,
                    f"🚀Адмінська розсилка {gen_hex_caption(admin_mail.id)} розпочата. Вам прийде повідомлення після її закінчення",
                    reply_markup=gen_ok("hide")
                )
                admin_mail.status = 1
                await admin_mails_db.update(admin_mail)
                bots = []
                bots_without_premium = [bot.token for bot in await bots_db.get_by(premium=0)]
                for bot_token in manager.bot_dict.keys():
                    if bot_token in bots_without_premium:
                        bots.append(manager.bot_dict[bot_token][0])
                create_task(gig.send_admin_mail(bots, admin_mail, admin_mail.sender))
        await sleep(5)


async def listen_mails_stats():
    while True:
        if gig.mails_stats_buffer:
            for mail_stats in gig.mails_stats_buffer:
                mail = await mails_db.get(mail_stats["mail_id"])
                await bot.send_message(
                    mail_stats["admin_id"],
                    f"Розсилка {gen_hex_caption(mail_stats['mail_id'])} в боті @{(await bots_db.get(mail.bot)).username} закінчена\n\n\
✅Надіслано: {mail_stats['sent_num']}\n💀Заблоковано: {mail_stats['blocked_num']}\n❌Помилка: {mail_stats['error_num']}\n\
⌛️Час розсилання: {mail_stats['elapsed_time']}",
                    reply_markup=gen_ok("hide")
                )
            gig.mails_stats_buffer = []
        await sleep(5)


async def listen_admin_mails_stats():
    while True:
        if gig.admin_mails_stats_buffer:
            for mail_stats in gig.admin_mails_stats_buffer:
                await bot.send_message(
                    mail_stats["admin_id"],
                    f"Розсилка {gen_hex_caption(mail_stats['mail_id'])} закінчена\n\
Надіслано: {mail_stats['sent_num']}\nЗаблоковано: {mail_stats['blocked_num']}\nПомилка: {mail_stats['error_num']}",
                    reply_markup=gen_ok("hide")
                )
            gig.admin_mails_stats_buffer = []
        await sleep(5)


async def listen_admin_notification_stats():
    while True:
        if admin_notification.admin_notification_stats:
            for notification_stats in admin_notification.admin_notification_stats:
                await bot.send_message(
                    notification_stats["admin_id"],
                    f"Сповіщення адмінів закінчено\n\
Надіслано: {notification_stats['sent_num']}\nЗаблоковано: {notification_stats['blocked_num']}\nПомилка: {notification_stats['error_num']}",
                    reply_markup=gen_ok("hide")
                )
            admin_notification.admin_notification_stats = []
        await sleep(5)


async def listen_purges_stats():
    while True:
        if gig.purges_stats_buffer != []:
            for purge_stats in gig.purges_stats_buffer:
                purge = await purges_db.get(purge_stats['purge_id'])
                if purge.mail_id:
                    await bot.send_message(
                        purge_stats["admin_id"],
                        f"Видалення {gen_hex_caption(purge_stats['purge_id'])} розсилки {gen_hex_caption(purge.mail_id)} в боті @{(await bots_db.get(purge.bot)).username} закінчено\n\n\
✅Очищено: {purge_stats['cleared_num']}\n❌Помилка: {purge_stats['error_num']}\n\
⌛️Час розсилання: {purge_stats['elapsed_time']}",
                        reply_markup=gen_ok("hide")
                    )
                else:
                    await bot.send_message(
                        purge_stats["admin_id"],
                        f"Чистка {gen_hex_caption(purge_stats['purge_id'])} в боті @{(await bots_db.get(purge.bot)).username} закінчена\n\n\
    ✅Очищено: {purge_stats['cleared_num']}\n❌Помилка: {purge_stats['error_num']}\n\
    ⌛️Час розсилання: {purge_stats['elapsed_time']}",
                        reply_markup=gen_ok("hide")
                    )
            gig.purges_stats_buffer = []
        await sleep(5)


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


async def run_listeners():
    create_task(listen_mails())
    create_task(listen_admin_mails())
    create_task(listen_purges())

    create_task(listen_admin_mails_stats())
    create_task(listen_mails_stats())
    create_task(listen_purges_stats())
    create_task(listen_admin_notification_stats())

    create_task(resume_action())
