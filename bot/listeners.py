from bot.misc import *
from bot.keyboards import gen_ok


async def listen_purges():
    while True:
        purges = await purges_db.get_all()
        for purge in purges:
            if purge.sched_dt and datetime.now(tz=ukraine_tz) > ukraine_tz.localize(purge.sched_dt):
                bot_dc = await bots_db.get(purge.bot)
                await purges_db.delete(purge.id)
                create_task(gig.clean(manager.bot_dict[bot_dc.token][0], purge, bot_dc.admin))
        await sleep(5)


async def listen_mails():
    while True:
        mails = await mails_db.get_all()
        for mail in mails:
            if mail.send_dt and datetime.now(tz=timezone('Europe/Kiev')) > ukraine_tz.localize(mail.send_dt):
                bot_dc = await bots_db.get(mail.bot)
                mail.active = 1
                await mails_db.update(mail)
                create_task(gig.send_mail(manager.bot_dict[bot_dc.token][0], mail, bot_dc.admin))
        await sleep(5)


async def listen_autodeletion():
    while True:
        msgs = [msg for msg in await msgs_db.get_all() if msg.del_dt != None]
        for msg in msgs:
            if datetime.now(tz=timezone('Europe/Kiev')) > ukraine_tz.localize(msg.del_dt):
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
        if gig.mails_stats_buffer != []:
            for mail_stats in gig.mails_stats_buffer:
                await bot.send_message(
                    mail_stats["admin_id"],
                    f"Розсилка {hex(mail_stats['mail_id'] * 1234)} закінчена\nНадіслано: {mail_stats['sent_num']}\n\
Заблоковано: {mail_stats['blocked_num']}\nПомилка: {mail_stats['error_num']}",
                    reply_markup=gen_ok("hide")
                )
            gig.mails_stats_buffer = []
        await sleep(5)


async def listen_purges_stats():
    while True:
        if gig.purges_stats_buffer != []:
            for purge_stats in gig.purges_stats_buffer:
                await bot.send_message(
                    purge_stats["admin_id"],
                    f"Чистка {hex(purge_stats['purge_id']*1234)} закінчена\n\
Очищено: {purge_stats['cleared_num']}\nПомилка: {purge_stats['error_num']}",
                    reply_markup=gen_ok("hide")
                )
            gig.purges_stats_buffer = []
        await sleep(5)
