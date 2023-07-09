from bot.misc import *
from bot.keyboards import bot_action, purge_action, gen_cancel, gen_ok
import bot.keyboards.purges as kb


async def safe_get_purge(uid: int, purge_id: int, cb_id: int | None = None) -> models.Purge | None:
    async def alert():
        if cb_id:
            await bot.answer_callback_query(
                cb_id,
                "❗️Помилка"
            )
        else:
            await bot.send_message(
                uid,
                "❗️Помилка",
                reply_markup=gen_ok("open_bot_list", "↩️Головне меню")
            )
    try:
        purge = await purges_db.get(purge_id)
    except data_exc.RecordIsMissing:
        await alert()
        return None
    if purge.active == 1:
        await alert()
        return None
    return purge


@dp.callback_query_handler(bot_action.filter(action="purges"))
async def open_purges_list(cb: CallbackQuery, callback_data: dict):
    bot_dc = await bots_db.get(int(callback_data["id"]))
    if bot_dc.premium <= 0:
        await cb.answer("⭐️Лише для преміум ботів")
        return
    purges = await purges_db.get_by(bot=int(callback_data["id"]))
    await cb.message.answer(
        "<i>💡Меню чисток. В цьому розділі можна створювати та запускати/заплановувати чистки. \
При виконанні чистки будуть видалятися всі коли-небудь надіслані ботом повідомлення за допомогою нашого сервісу. \
Варто пам'ятати, що повідомлення старіші за 48 год. не можуть бути видалені.</i>\n\n\
<b>♻️Список чисток:</b>",
        reply_markup=kb.gen_purge_list(bot_dc, purges)
    )
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


async def open_purge_menu(uid: int, purge_id: int, msg_id: int):
    purge = await purges_db.get(purge_id)
    await bot.send_message(
        uid,
        f"♻️Чистка: {hex(purge.id * 1234)}\n\
🕑Заплановано на: {purge.sched_dt.strftime(models.DT_FORMAT) if purge.sched_dt else 'немає'}",
        reply_markup=kb.gen_purge_menu(purge)
    )
    await safe_del_msg(uid, msg_id)


@dp.callback_query_handler(bot_action.filter(action="add_purge"))
async def add_purge(cb: CallbackQuery, callback_data: dict):
    purge = models.Purge(
        0,
        int(callback_data["id"])
    )
    await purges_db.add(purge)
    await open_purge_menu(cb.from_user.id, purge.id, cb.message.message_id)


@dp.callback_query_handler(purge_action.filter(action="open_menu"), state="*")
async def open_purge_menu_cb(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    purge = await safe_get_purge(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not purge:
        return
    await state.set_state(None)
    await open_purge_menu(cb.from_user.id, int(callback_data["id"]), cb.message.message_id)


@dp.callback_query_handler(purge_action.filter(action="delete_purge"))
async def delete_purge(cb: CallbackQuery, callback_data: dict):
    purge = await safe_get_purge(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not purge:
        return
    purge = await purges_db.get(int(callback_data["id"]))
    await purges_db.delete(purge.id)
    callback_data["id"] = purge.bot
    await open_purges_list(cb, callback_data)


@dp.callback_query_handler(purge_action.filter(action="schedule"))
async def schedule_purge(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    purge = await safe_get_purge(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not purge:
        return
    msg = await cb.message.answer(
        "Введіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
        reply_markup=gen_cancel(purge_action.new(callback_data["id"], "open_menu"))
    )
    await state.set_state(states.InputStateGroup.purge_sched_dt)
    await state.set_data({"purge_id": int(callback_data["id"]), "msg_id": msg.message_id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.purge_sched_dt)
async def edit_sched_dt(msg: Message, state: FSMContext):
    await safe_del_msg(msg.from_user.id, msg.message_id)
    state_data = await state.get_data()
    purge = await safe_get_purge(msg.from_user.id, state_data["purge_id"])
    if not purge:
        return
    try:
        input_dt = datetime.strptime(msg.text, models.DT_FORMAT)
    except ValueError:
        await safe_edit_message(
            "❗️Невірний формат. Спробуйте ще раз\n\nВведіть дату та час у форматі <i>[H:M d.m.Y]</i>\n\
Приклад: <i>16:20 12.05.2023</i>",
            msg.from_user.id,
            state_data["msg_id"],
            reply_markup=gen_cancel(purge_action.new(purge.id, "open_menu"))
        )
        return
    if tz.localize(input_dt) < datetime.now(tz=tz):
        await safe_edit_message(
            "❗️Введена дата не може бути у минулому. Спробуйте ще раз\n\
Введіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
            msg.from_user.id,
            state_data["msg_id"],
            reply_markup=gen_cancel(purge_action.new(purge.id, "open_menu"))
        )
        return
    purge.sched_dt = datetime.strptime(msg.text, models.DT_FORMAT)
    await state.set_state(None)
    await purges_db.update(purge)
    await open_purge_menu(msg.from_user.id, purge.id, state_data["msg_id"])


@dp.callback_query_handler(purge_action.filter(action="run"))
async def run(cb: CallbackQuery, callback_data: dict):
    purge = await safe_get_purge(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not purge:
        return
    bot_dc = await bots_db.get(purge.bot)
    await cb.message.answer(
        f"🚀Чистка {gen_hex_caption(purge.id)} розпочата. Вам прийде повідомлення після її закінчення",
        reply_markup=gen_ok(bot_action.new(
            bot_dc.id,
            "purges"
        ))
    )
    await safe_del_msg(cb.from_user.id, cb.message.message_id)
    create_task(gig.clean(manager.bot_dict[bot_dc.token][0], purge, cb.from_user.id))
