from bot.misc import *
from bot.keyboards import bot_action, gen_confirmation
from bot.keyboards import settings as kb

from bot.handlers.menu import open_bot_list


@dp.callback_query_handler(bot_action.filter(action="settings"))
async def open_settings(cb: CallbackQuery, callback_data: dict):
    bot_dc = bots_db.get(int(callback_data["id"]))
    await cb.message.answer(
        "Налаштування",
        reply_markup=kb.gen_settings_menu(bot_dc)
    )
    try:
        await cb.message.delete()
    except MessageCantBeDeleted:
        pass


@dp.callback_query_handler(bot_action.filter(action="delete_bot"))
async def delete_bot(cb: CallbackQuery, callback_data: dict):
    bot_dc = bots_db.get(int(callback_data["id"]))
    await cb.message.answer(
        "Ви впевнені, що хочете видалити бота?",
        reply_markup=gen_confirmation(
            bot_action.new(bot_dc.id, "confirm_deletion"),
            bot_action.new(bot_dc.id, "open_menu")
        )
    )
    try:
        await cb.message.delete()
    except MessageCantBeDeleted:
        pass


@dp.callback_query_handler(bot_action.filter(action="confirm_deletion"))
async def deletion_confirm(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    bot_dc = bots_db.get(int(callback_data["id"]))
    bot_dc.admin = None
    bots_db.update(bot_dc)
    await open_bot_list(cb, state)
