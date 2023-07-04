from bot.misc import *
from bot.keyboards import bot_action, gen_confirmation
from bot.keyboards import settings as kb

from bot.handlers.menu import open_bot_list


@dp.callback_query_handler(bot_action.filter(action="settings"))
async def open_settings(cb: CallbackQuery, callback_data: dict):
    bot_dc = await bots_db.get(int(callback_data["id"]))
    await cb.message.answer(
        "<b>⚙️Меню налаштувань:</b>\n\n\
<i>▸ Автоприйом- бот автоматично приймає заявки на вступ в канал.\n\
▸ Збір користувачів- бот записує в базу даних користувачів після проходження капчі.\n\
▸ Видалити бота- видаляє бота з профілю. Видаленого бота можна заново додати в профіль без втрати даних.\n</i>",
        reply_markup=kb.gen_settings_menu(bot_dc)
    )
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.callback_query_handler(bot_action.filter(action="delete_bot"))
async def delete_bot(cb: CallbackQuery, callback_data: dict):
    bot_dc = await bots_db.get(int(callback_data["id"]))
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
    bot_dc = await bots_db.get(int(callback_data["id"]))
    await manager.delete_webhook(bot_dc)
    bot_dc.admin = None
    bot_status = 0
    await bots_db.update(bot_dc)
    await open_bot_list(cb, state)


@dp.callback_query_handler(bot_action.filter(action="autoapprove_on"))
async def approve_on(cb: CallbackQuery, callback_data: dict):
    bot_dc = await bots_db.get(int(callback_data["id"]))
    bot_dc.settings.set_autoapprove(True)
    await bots_db.update(bot_dc)
    await open_settings(cb, callback_data)


@dp.callback_query_handler(bot_action.filter(action="autoapprove_off"))
async def approve_off(cb: CallbackQuery, callback_data: dict):
    bot_dc = await bots_db.get(int(callback_data["id"]))
    bot_dc.settings.set_autoapprove(False)
    await bots_db.update(bot_dc)
    await open_settings(cb, callback_data)


@dp.callback_query_handler(bot_action.filter(action="users_collect_on"))
async def users_collect_on(cb: CallbackQuery, callback_data: dict):
    bot_dc = await bots_db.get(int(callback_data["id"]))
    bot_dc.settings.set_users_collect(True)
    await bots_db.update(bot_dc)
    await open_settings(cb, callback_data)


@dp.callback_query_handler(bot_action.filter(action="users_collect_off"))
async def users_collect_off(cb: CallbackQuery, callback_data: dict):
    await cb.answer("👩‍💻In development")
    # bot_dc = await bots_db.get(int(callback_data["id"]))
    # bot_dc.settings.set_users_collect(False)
    # await bots_db.update(bot_dc)
    # await open_settings(cb, callback_data)
