from bot.misc import *
from bot.keyboards import gen_ok


async def listen_purges():
    while True:
        purges = purges_db.get_all()
        for purge in purges:
            if purge.sched_dt and datetime.now(tz=ukraine_tz) > ukraine_tz.localize(purge.sched_dt):
                bot_dc = bots_db.get(purge.bot)
                purges_db.delete(purge.id)
                cleared_num, error_num = await gig.clean(manager.bot_dict[bot_dc.token][0], purge)
                await bot.send_message(
                    bot_dc.admin,
                    f"Чистка {hex(purge.id * 1234)} закінчена\nОчищено: {cleared_num}\nПомилка:{error_num}",
                    reply_markup=gen_ok("hide")
                )
        await sleep(5)


async def listen_mails():
    while True:
        mails = mails_db.get_all()
        for mail in mails:
            if mail.send_dt and datetime.now(tz=timezone('Europe/Kiev')) > ukraine_tz.localize(mail.send_dt):
                bot_dc = bots_db.get(mail.bot)
                mails_db.delete(mail.id)
                sent_num, blocked_num, error_num = await gig.send_mail(manager.bot_dict[bot_dc.token][0], mail)
                await bot.send_message(
                    bot_dc.admin,
                    f"Розсилка {hex(mail.id * 1234)} закінчена\nНадіслано: {sent_num}\nЗаблоковано:{blocked_num}\nПомилка:{error_num}",
                    reply_markup=gen_ok("hide")
                )
        await sleep(5)
