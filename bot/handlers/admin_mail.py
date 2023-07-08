import bot.handlers.settings
from bot.misc import *
from bot.keyboards import admin_mail as adm
from bot.keyboards import bot_action
from bot.keyboards import gen_cancel, admin_bot_action, gen_ok


@dp.callback_query_handler(lambda cb: cb.data == "admin_mail")
async def menu_admin_mails(cb: CallbackQuery):
    await cb.message.answer(
        "Hello",
        reply_markup=adm.gen_admin_mail_list()
    )
    await cb.message.delete()