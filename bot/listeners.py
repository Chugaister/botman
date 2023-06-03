from bot.misc import *


async def listen_purges():
    while True:
        purges = purges_db.get_all()
        for purge in purges:
            if purge.sched_dt and datetime.now(tz=ukraine_tz) > ukraine_tz.localize(purge.sched_dt):
                bot_dc = bots_db.get(purge.bot)
                await gig.clean(manager.bot_dict[bot_dc.token][0], purge)
        await sleep(5)


async def listen_mails():
    while True:
        mails = mails_db.get_all()
        for mail in mails:
            if mail.send_dt and datetime.now(tz=timezone('Europe/Kiev')) > ukraine_tz.localize(mail.send_dt):
                bot_dc = bots_db.get(mail.bot)
                await gig.send_mail(manager.bot_dict[bot_dc.token][0], mail)
        await sleep(5)
