from bot.misc import *
from bot.keyboards import bot_action, gen_confirmation
from bot.keyboards import settings as kb

from bot.handlers.menu import open_bot_list


@dp.callback_query_handler(bot_action.filter(action="settings"))
async def open_settings(cb: CallbackQuery, callback_data: dict):
    bot_dc = await bots_db.getFromDB(int(callback_data["id"]))
    await cb.message.answer(
        "{text9}Налаштування",
        reply_markup=kb.gen_settings_menu(bot_dc)
    )
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.callback_query_handler(bot_action.filter(action="delete_bot"))
async def delete_bot(cb: CallbackQuery, callback_data: dict):
    bot_dc = await bots_db.getFromDB(int(callback_data["id"]))
    await manager.delete_webhook(bot_dc)
    await cb.message.answer(
        "Ви впевнені, що хочете видалити бота?",
        reply_markup=gen_confirmation(
            bot_action.new(bot_dc.id, "confirm_deletion"),
            bot_action.new(bot_dc.id, "open_menu")
        )
    )
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.callback_query_handler(bot_action.filter(action="confirm_deletion"))
async def deletion_confirm(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    bot_dc = await bots_db.getFromDB(int(callback_data["id"]))
    await manager.delete_webhook(bot_dc)
    bot_dc.admin = None
    bot_status = 0
    await bots_db.updateInDB(bot_dc)
    await open_bot_list(cb, state)
