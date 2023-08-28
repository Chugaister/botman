import bot.handlers.settings
from bot.misc import *
from bot.keyboards import admin_panel as kb
from bot.keyboards import gen_cancel, admin_bot_action, gen_ok


@dp.callback_query_handler(lambda cb: cb.from_user.id in config.admin_list and cb.data == "admin", state="*")
async def send_admin_panel(cb: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    await cb.message.answer(
        "Адмін-панель",
        reply_markup=kb.admin_panel_menu
    )
    await cb.message.delete()


@dp.message_handler(lambda msg: msg.from_user.id in config.admin_list, commands="admin")
async def send_admin_panel(msg: Message):
    await msg.answer(
        "Адмін-панель",
        reply_markup=kb.admin_panel_menu
    )
    await msg.delete()


@dp.callback_query_handler(lambda cb: cb.data == "bots_admin")
async def set_premium(cb: CallbackQuery, state: FSMContext):
    text = "Боти в системі:\n\n"
    ubot_dc_list = await bots_db.get_all()
    for ubot_dc in ubot_dc_list:
        text += "\t@" + ubot_dc.username + "\n\n"
    text += "Введіть юзернейм бота"
    msg = await cb.message.answer(
        text,
        reply_markup=gen_cancel("admin")
    )
    await state.set_state(states.InputStateGroup.bot_username)
    await state.set_data({"msg_id": msg.message_id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


async def send_adminbot_panel(uid: int, bot_id: int, msg_id: int):
    bot_dc = await bots_db.get(bot_id)
    try:
        admin = await admins_db.get(bot_dc.admin)
    except data_exc.RecordIsMissing:
        admin = models.Admin(0, "видалено", "", "")
    await bot.send_message(
        uid,
        f"🤖 @{bot_dc.username}\n🆔 {bot_dc.id}\n👤@{admin.username}\n👑Преміум {bot_dc.premium}\n",
        reply_markup=kb.gen_admin_bot_menu(bot_dc)
    )
    await safe_del_msg(uid, msg_id)


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.bot_username)
async def bot_username_input(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    bot_username = msg.text.replace("@", "")
    bot_list = await bots_db.get_by(username=bot_username)
    await msg.delete()
    if bot_list == []:
        await msg.answer(
            f"Бота з юзернеймом {msg.text} не знайдено",
            reply_markup=gen_ok("hide")
        )
        return
    bot_dc = bot_list[0]
    await send_adminbot_panel(msg.from_user.id, bot_dc.id, state_data["msg_id"])
    await state.set_state(None)


@dp.callback_query_handler(admin_bot_action.filter(action="ban"))
async def ban_bot(cb: CallbackQuery, callback_data: dict):
    bot_dc = await bots_db.get(int(callback_data["id"]))
    bot_dc.status = -1
    await bots_db.update(bot_dc)
    await send_adminbot_panel(cb.from_user.id, bot_dc.id, cb.message.message_id)


@dp.callback_query_handler(admin_bot_action.filter(action="unban"))
async def unban_bot(cb: CallbackQuery, callback_data: dict):
    bot_dc = await bots_db.get(int(callback_data["id"]))
    bot_dc.status = 1
    await bots_db.update(bot_dc)
    await send_adminbot_panel(cb.from_user.id, bot_dc.id, cb.message.message_id)


@dp.callback_query_handler(admin_bot_action.filter(action="premium_add"))
async def premium_add(cb: CallbackQuery, callback_data: dict):
    bot_dc = await bots_db.get(int(callback_data["id"]))
    bot_dc.premium = 1
    await bots_db.update(bot_dc)
    await send_adminbot_panel(cb.from_user.id, bot_dc.id, cb.message.message_id)


@dp.callback_query_handler(admin_bot_action.filter(action="premium_sub"))
async def premium_sub(cb: CallbackQuery, callback_data: dict):
    bot_dc = await bots_db.get(int(callback_data["id"]))
    bot_dc.premium = 0
    await bots_db.update(bot_dc)
    await send_adminbot_panel(cb.from_user.id, bot_dc.id, cb.message.message_id)


@dp.callback_query_handler(lambda cb: cb.data == "hide", state="*")
async def hide(cb: CallbackQuery):
    await safe_del_msg(cb.from_user.id, cb.message.message_id)

