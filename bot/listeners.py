from bot.misc import *
from bot.keyboards import gen_ok
from bot.handlers import admin_notification

from logging import getLogger
import subprocess
import os


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


async def listen_purges():
    while True:
        purges = await purges_db.get_all()
        for purge in purges:
            if purge.sched_dt and datetime.now(tz=tz) > tz.localize(purge.sched_dt)\
            and purge.active != 1:
                purge.active = 1
                await purges_db.update(purge)
                bot_dc = await bots_db.get(purge.bot)
                await bot.send_message(
                    bot_dc.admin,
                    f"🚀Чистка {gen_hex_caption(purge.id)} розпочата. Вам прийде повідомлення після її закінчення",
                    reply_markup=gen_ok("hide")
                )
                create_task(gig.clean(manager.bot_dict[bot_dc.token][0], purge, bot_dc.admin))
        await sleep(5)


logger = getLogger("aiogram")
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
            if mail.send_dt and datetime.now(tz=timezone('Europe/Kiev')) > tz.localize(mail.send_dt) and not mail.active and not mail.status:
                await gig.enqueue_mail(mail)
                bot_dc = await bots_db.get(mail.bot)
                await bot.send_message(
                    bot_dc.admin,
                    f"Розсилка {gen_hex_caption(mail.id)} була поставлена в чергу. Вам прийде повідомлення коли вона розпочнеться",
                    reply_markup=gen_ok("hide")
                )

            bot_dc = await bots_db.get(mail.bot)
            if not bot_dc.action and mail.active and not mail.status:
                await bot.send_message(
                    bot_dc.admin,
                     f"🚀Розсилка {gen_hex_caption(mail.id)} розпочата. Вам прийде повідомлення після її закінчення",
                    reply_markup=gen_ok("hide")
                )
                mail.status = 1
                await mails_db.update(mail)
                bot_dc.action = f"mail_{mail.id}"
                await bots_db.update(bot_dc)
                ubot = manager.bot_dict[(await bots_db.get_by(id=mail.bot))[0].token][0]
                create_task(gig.send_mail(ubot, mail, bot_dc.admin))
        await sleep(5)


async def listen_autodeletion():
    while True:
        msgs = [msg for msg in await msgs_db.get_all() if msg.del_dt != None]
        for msg in msgs:
            if datetime.now(tz=timezone('Europe/Kiev')) > tz.localize(msg.del_dt):
                bot_dc = await bots_db.get(msg.bot)
                try:
                    await manager.bot_dict[bot_dc.token][0].delete_message(
                        msg.user,
                        msg.id
                    )
                except Exception:
                    pass
                await msgs_db.delete(msg.id)
        await sleep(5)


async def listen_mails_stats():
    while True:
        if gig.mails_stats_buffer:
            for mail_stats in gig.mails_stats_buffer:
                await bot.send_message(
                    mail_stats["admin_id"],
                    f"Розсилка {gen_hex_caption(mail_stats['mail_id'])} закінчена\n\
✅Надіслано: {mail_stats['sent_num']}\n💀Заблоковано: {mail_stats['blocked_num']}\n❌Помилка: {mail_stats['error_num']}\n\
⌛️Час розсилання: {mail_stats['elapsed_time']}",
                    reply_markup=gen_ok("hide")
                )
            gig.mails_stats_buffer = []
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
                await bot.send_message(
                    purge_stats["admin_id"],
                    f"Чистка {gen_hex_caption(purge_stats['purge_id'])} закінчена\n\
Очищено: {purge_stats['cleared_num']}\nПомилка: {purge_stats['error_num']}",
                    reply_markup=gen_ok("hide")
                )
            gig.purges_stats_buffer = []
        await sleep(5)


async def listen_mails_on_startup():
    ubots = []
    ubots_all = await bots_db.get_all()
    for ubot in ubots_all:
        if ubot.status == 1 and ubot.admin:
            ubots.append(ubot)
    mails = await mails_db.get_all()
    for mail in mails:
        mail_msgs = await mails_queue_db.get_by(mail_id=mail.id, admin_status=False)
        if mail_msgs:
            for ubot in ubots:
                mail_bot_msgs = await mails_queue_db.get_by(bot=ubot.id, mail_id=mail.id, admin_status=False)
                if ubot.action == f"mail_{mail.id}" and mail_bot_msgs:
                    bot_dc = manager.bot_dict[(await bots_db.get_by(id=mail.bot))[0].token][0]
                    create_task(gig.send_mail(bot_dc, mail, ubot.admin))
                elif ubot.action == f"mail_{mail.id}" and not mail_bot_msgs:
                    ubot.action = None
                    await bots_db.update(ubot)


async def run_listeners():
    create_task(listen_mails())
    create_task(listen_purges())
    create_task(listen_autodeletion())
    create_task(listen_mails_stats())
    create_task(listen_purges_stats())
    create_task(listen_admin_notification_stats())
    create_task(listen_mails_on_startup())
