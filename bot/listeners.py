from bot.misc import *
from bot.keyboards import gen_ok
from bot.handlers import admin_notification


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


async def listen_mails():
    while True:
        mails = await mails_db.get_all()
        for mail in mails:
            if mail.send_dt and datetime.now(tz=timezone('Europe/Kiev')) > tz.localize(mail.send_dt):
                users = await user_db.get_by(bot=mail.bot)
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
                bot_dc = await bots_db.get(mail.bot)
                await bot.send_message(
                    bot_dc.admin,
                    f"Розсилка {gen_hex_caption(mail.id)} була поставлена в чергу. Вам прийде повідомлення коли вона розпочнеться",
                    reply_markup=gen_ok("hide")
                )

            bot_dc = await bots_db.get(mail.bot)
            if not bot_dc.action and mail.active:
                await bot.send_message(
                            bot_dc.admin,
                                 f"🚀Розсилка {gen_hex_caption(mail.id)} розпочата. Вам прийде повідомлення після її закінчення",
                                reply_markup=gen_ok("hide")
                )
                if not bot_dc.action:
                    bot_dc.action = f"mail_{mail.id}"
                    await bots_db.update(bot_dc)
                ubot = manager.bot_dict[(await bots_db.get_by(id=mail.bot))[0].token][0]
                create_task(gig.send_mail(ubot, mail, bot_dc.admin))

        await sleep(5)


# async def listen_admin_mails():
#     while True:
#         admin_mails = await mails_db.get_all()
#         for admin_mail in admin_mails:
#             if admin_mail.send_dt and datetime.now(tz=timezone('Europe/Kiev')) > tz.localize(admin_mail.send_dt):
#                 bots = [ubot for ubot in await bots_db.get_by(premium=0)]
#                 for ubot in bots:
#                     users = await user_db.get_by(bot=ubot.id)
#                     for user in users:
#                         new_mail_msgs = models.MailsQueue(
#                             _id=0,
#                             bot=admin_mail.bot,
#                             user=user.id,
#                             mail_id=admin_mail.id,
#                             admin_status=True
#                         )
#                         await mails_queue_db.add(new_mail_msgs)
#                     admin_mail.active = 1
#                     await mails_db.update(admin_mail)
#             if admin_mail.active and not admin_mail.status:
#                 await bot.send_message(
#                             admin_mail.sender,
#                                  f"🚀Адмінська розсилка {gen_hex_caption(admin_mail.id)} розпочата. Вам прийде повідомлення після її закінчення",
#                                 reply_markup=gen_ok("hide")
#                             )
#                 bots = []
#                 bots_without_premium = [bot.token for bot in await bots_db.get_by(premium=0)]
#                 for bot_token in manager.bot_dict.keys():
#                     if bot_token in bots_without_premium:
#                         bots.append(manager.bot_dict[bot_token][0])
#                 create_task(gig.send_mail(admin_mail, admin_mail.sender, bots))
#                 admin_mail.status = 1
#                 await admin_mails_db.update(admin_mail)
#             mail_msgs = await mails_queue_db.get_by(mail_id=admin_mail.id, admin_status=True)
#             bots = [ubot for ubot in await bots_db.get_by(premium=0)]
#             for ubot in bots:
#                 if ubot.action == f"admin_mail_{admin_mail.id}" and mail_msgs:
#                     create_task(gig.send_mail(admin_mail, admin_mail.sender))
#
#
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
                except:
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
Надіслано: {mail_stats['sent_num']}\nЗаблоковано: {mail_stats['blocked_num']}\nПомилка: {mail_stats['error_num']}",
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
                await bot.send_message(
                    purge_stats["admin_id"],
                    f"Чистка {gen_hex_caption(purge_stats['purge_id'])} закінчена\n\
Очищено: {purge_stats['cleared_num']}\nПомилка: {purge_stats['error_num']}",
                    reply_markup=gen_ok("hide")
                )
            gig.purges_stats_buffer = []
        await sleep(5)


async def listen_mails_on_startup():
    print("start listener mails queue")
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
                if ubot.action == f"mail_{mail.id}" and mail_msgs:
                    bot_dc = manager.bot_dict[(await bots_db.get_by(id=mail.bot))[0].token][0]
                    create_task(gig.send_mail(bot_dc, mail, ubot.admin))


async def run_listeners():
    create_task(listen_mails())
    # create_task(listen_admin_mails())
    create_task(listen_purges())
    create_task(listen_autodeletion())
    create_task(listen_admin_mails_stats())
    create_task(listen_mails_stats())
    create_task(listen_purges_stats())
    create_task(listen_admin_notification_stats())
    create_task(listen_mails_on_startup())
