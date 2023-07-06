import bot.handlers.mails
from bot.misc import *
from bot.keyboards import menu as kb
from bot.keyboards import gen_cancel


@dp.message_handler(commands="start")
async def send_start(msg: Message):
    try:
        await admins_db.add(
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
        "<b>🚀Сервіс автоматизованої реклами</b>\n\n\
<i>💡Аби скористатися сервісом, вам потрібно створити власного бота, \
додати його в адміністратори каналу і у наш сервіс. \
Варто зазначити, що канал повинен бути закритим (доступ лише після подачі заявки на вступ)</i>\n\n\
Доступний функціонал:\n\
    ▸ Каптча\n\
    ▸ Привітання\n\
    ▸ Розсилка\n\
    ▸ Чистка\n\
",
        reply_markup=kb.go_to_bot_list
    )
    await safe_del_msg(msg.from_user.id, msg.message_id)


async def open_bot_list(uid: int, msg_id: int):
    bots = await bots_db.get_by(admin=uid)
    await bot.send_message(
        uid,
        "<b>🤖Меню ботів</b>\n\n\
<i>💡Ви можете додавати до нашого сервісу довільну кількість ботів. \
Варто нагадати, що на один канал має припадати не більше одного бота-адміністратора, \
але один бот може бути адміністратором декількох каналів. \
Важливо щоб бот був підключений лише до нашого сервісу, інакше виникатимуть конфілкти</i>",
        reply_markup=kb.gen_bot_list(bots)
    )
    await safe_del_msg(uid, msg_id)


@dp.callback_query_handler(lambda cb: cb.data == "open_bot_list", state="*")
async def open_bot_list_cb(cb: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    await open_bot_list(cb.from_user.id, cb.message.message_id)


@dp.message_handler(commands="mybots")
async def open_bot_list_msg(msg: Message, state: FSMContext):
    await state.set_state(None)
    await open_bot_list(msg.from_user.id, msg.message_id)


@dp.callback_query_handler(lambda cb: cb.data == "start_msg")
async def back_to_start_msg(cb: CallbackQuery):
    cb.message.from_user = cb.from_user
    await send_start(cb.message)


@dp.callback_query_handler(lambda cb: cb.data == "add_bot")
async def add_bot(cb: CallbackQuery, state: FSMContext):
    msg = await cb.message.answer(
        "💡Аби скористатися сервісом вам потрібно створити бота за допомогою @BotFather і додати його в адміністратори каналу. \
Після створення бота скопіюйте токен бота і надішліть його сюди",
        reply_markup=gen_cancel("open_bot_list")
    )
    await state.set_state(states.InputStateGroup.token)
    await state.set_data({"msg_id": msg.message_id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


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
                "❗️Помилка, спробуйте ще раз.\n\
💡Аби скористатися сервісом вам потрібно створити бота за допомогою @BotFather і додати його в адміністратори каналу. \
Після створення бота скопіюйте токен бота і надішліть його сюди",
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
    )
    try:
        await bots_db.add(bot_dc)
        captchas = await captchas_db.get_by(bot=bot_dc.id)
        if captchas == []:
            captcha = models.Captcha(
                0,
                bot_dc.id,
                text="Аби увійти в канал, підтвердіть, що ви не робот",
                buttons="✅ Я не робот"
            )
            await captchas_db.add(captcha)
    except data_exc.RecordAlreadyExists:
        bot_dc = await bots_db.get(info["id"])
        bot_dc.admin = msg.from_user.id
        bot_dc.status = 1
        await bots_db.update(bot_dc)
    manager.register_handlers([bot_dc])
    await manager.set_webhook([bot_dc])
    await state.set_state(None)
    await open_bot_menu(msg.from_user.id, bot_dc.id, state_data["msg_id"])


async def open_bot_menu(uid: int, bot_id: int, msg_id: int, callback_query_id: int = None):
    bot_dc = await bots_db.get(bot_id)
    if bot_dc.status == -1 and uid not in config.admin_list:
        return
    try:
        admin = await admins_db.get(bot_dc.admin)
    except data_exc.RecordIsMissing:
        admin = models.Admin(0, "видалено", "", "")
    users = await user_db.get_by(bot=bot_dc.id)
    all_users, active, dead, joined_today, joined_week, joined_month = gen_stats(users)
    table = PrettyTable()
    table.field_names = ["Юзери", "Кількість"]
    table.add_rows([
        ["Всього", all_users],
        ["Активних", active],
    ])
    table.add_row(["Мертвих", dead], divider=True)
    table.add_rows([
        ["Сьогодні", f'+{joined_today}'],
        ["Тиждень", f'+{joined_week}'], 
        ["Місяць", f'+{joined_month}']])
    await bot.send_message(
        uid,
        f"🤖 @{bot_dc.username}\n🆔 {bot_dc.id}\n👤@{admin.username}\n👑Преміум {bot_dc.premium}\n\n📊Статистика:\n<code>{table}</code>",
        reply_markup=kb.gen_bot_menu(bot_dc)
    )
    await safe_del_msg(uid, msg_id)


@dp.callback_query_handler(kb.bot_action.filter(action="open_menu"), state="*")
async def open_bot_menu_cb(cb: CallbackQuery, callback_data: dict):
    await open_bot_menu(cb.from_user.id, int(callback_data["id"]), cb.message.message_id, cb.id)
