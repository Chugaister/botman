import bot.handlers.mails
from bot.misc import *
from bot.keyboards import menu as kb
from bot.keyboards import gen_cancel


@dp.message_handler(commands="start")
async def send_start(msg: Message):
    try:
        admins_db.add(
            models.Admin(
                msg.from_user.id,
                msg.from_user.username,
                msg.from_user.first_name,
                msg.from_user.last_name
            )
        )
    except data_exc.RecordAlreadyExists:
        pass
    await msg.answer(
        "Опис",
        reply_markup=kb.go_to_bot_list
    )
    try:
        await msg.delete()
    except MessageCantBeDeleted:
        pass


@dp.callback_query_handler(lambda cb: cb.data == "open_bot_list", state="*")
async def open_bot_list(cb: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    bots = bots_db.get_by(admin=cb.from_user.id)
    await cb.message.answer(
        "Список ботів:",
        reply_markup=kb.gen_bot_list(bots)
    )
    try:
        await cb.message.delete()
    except MessageCantBeDeleted:
        pass


@dp.callback_query_handler(lambda cb: cb.data == "start_msg")
async def back_to_start_msg(cb: CallbackQuery):
    cb.message.from_user = cb.from_user
    await send_start(cb.message)


@dp.callback_query_handler(lambda cb: cb.data == "add_bot")
async def add_bot(cb: CallbackQuery, state: FSMContext):
    msg = await cb.message.answer(
        "Надішліть токен бота",
        reply_markup=gen_cancel("open_bot_list")
    )
    await state.set_state(states.InputStateGroup.token)
    await state.set_data({"msg_id": msg.message_id})
    try:
        await cb.message.delete()
    except MessageCantBeDeleted:
        pass


def token_validation(msg: Message):
    return True


@dp.message_handler(token_validation, content_types=ContentTypes.TEXT, state=states.InputStateGroup.token)
async def token_input(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    req = get(f"https://api.telegram.org/bot{msg.text}/getMe")
    await msg.delete()
    if not req.ok:
        try:
            await bot.edit_message_text(
                "Невірний формат. Повторіть спробу\nНадішліть токен бота",
                msg.from_user.id,
                state_data["msg_id"],
                reply_markup=gen_cancel("open_bot_list")
            )
        except MessageNotModified:
            pass
        return
    info = req.json()["result"]
    bot_dc = models.Bot(
        info["id"],
        msg.text,
        info["username"],
        msg.from_user.id,
        0,
        0
    )
    try:
        bots_db.add(bot_dc)
    except data_exc.RecordAlreadyExists:
        bot_dc = bots_db.get(info["id"])
        bot_dc.admin = msg.from_user.id
        bots_db.update(bot_dc)
    await state.set_state(None)
    await open_bot_menu(msg.from_user.id, bot_dc.id, state_data["msg_id"])


async def open_bot_menu(uid: int, bot_id: int, msg_id: int, callback_query_id: int = None):
    bot_dc = bots_db.get(bot_id)
    if bot_dc.premium == -1 and uid not in config.admin_list:
        return
    try:
        admin = admins_db.get(bot_dc.admin)
    except data_exc.RecordIsMissing:
        admin = models.Admin(0, "видалено", "", "")
    users = user_db.get_by(bot=bot_dc.id)
    all_users, active, dead = gen_stats(users)
    table = PrettyTable()
    table.field_names = ["Юзери", "Кількість"]
    table.add_rows([
        ["Всього", all_users],
        ["Активних", active],
        ["Мертвих", dead]
    ])
    await bot.send_message(
        uid,
        f"🤖 @{bot_dc.username}\n🆔 {bot_dc.id}\n👤@{admin.username}\n👑Преміум {bot_dc.premium}\n\n📊Статистика:\n<code>{table}</code>",
        reply_markup=kb.gen_bot_menu(bot_dc)
    )
    try:
        await bot.delete_message(
            uid,
            msg_id
        )
    except MessageCantBeDeleted:
        pass


@dp.callback_query_handler(kb.bot_action.filter(action="open_menu"), state="*")
async def open_bot_menu_cb(cb: CallbackQuery, callback_data: dict):
    await open_bot_menu(cb.from_user.id, int(callback_data["id"]), cb.message.message_id, cb.id)
