from bot.misc import *
from bot.keyboards import bot_action, purge_action, gen_cancel, gen_ok
import bot.keyboards.purges as kb


@dp.callback_query_handler(bot_action.filter(action="purges"))
async def open_purges_list(cb: CallbackQuery, callback_data: dict):
    bot_dc = bots_db.get(int(callback_data["id"]))
    if bot_dc.premium <= 0:
        await cb.answer("⭐️Лише для преміум ботів")
        return
    purges = purges_db.get_by(bot=int(callback_data["id"]))
    await cb.message.answer(
        "{text8}\nЧистки:",
        reply_markup=kb.gen_purge_list(bot_dc, purges)
    )
    try:
        await cb.message.delete()
    except MessageCantBeDeleted:
        pass


async def open_purge_menu(uid: int, purge_id: int, msg_id: int):
    purge = purges_db.get(purge_id)
    await bot.send_message(
        uid,
        f"♻️Чистка: {hex(purge.id * 1234)}\n\
🕑Заплановано на: {purge.sched_dt.strftime(models.DT_FORMAT) if purge.sched_dt else 'немає'}",
        reply_markup=kb.gen_purge_menu(purge)
    )
    try:
        await bot.delete_message(uid, msg_id)
    except MessageCantBeDeleted:
        pass


@dp.callback_query_handler(bot_action.filter(action="add_purge"))
async def add_purge(cb: CallbackQuery, callback_data: dict):
    purge = models.Purge(
        0,
        int(callback_data["id"])
    )
    purges_db.add(purge)
    await open_purge_menu(cb.from_user.id, purge.id, cb.message.message_id)


@dp.callback_query_handler(purge_action.filter(action="open_menu"), state="*")
async def open_purge_menu_cb(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.set_state(None)
    await open_purge_menu(cb.from_user.id, int(callback_data["id"]), cb.message.message_id)


@dp.callback_query_handler(purge_action.filter(action="delete_purge"))
async def delete_purge(cb: CallbackQuery, callback_data: dict):
    purge = purges_db.get(int(callback_data["id"]))
    purges_db.delete(purge.id)
    callback_data["id"] = purge.bot
    await open_purges_list(cb, callback_data)


@dp.callback_query_handler(purge_action.filter(action="schedule"))
async def schedule_purge(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    msg = await cb.message.answer(
        "Введіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
        reply_markup=gen_cancel(purge_action.new(callback_data["id"], "open_menu"))
    )
    await state.set_state(states.InputStateGroup.purge_sched_dt)
    await state.set_data({"purge_id": int(callback_data["id"]), "msg_id": msg.message_id})
    try:
        await cb.message.delete()
    except MessageCantBeDeleted:
        pass


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.purge_sched_dt)
async def edit_sched_dt(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    purge = purges_db.get(state_data["purge_id"])
    await msg.delete()
    try:
        purge.sched_dt = datetime.strptime(msg.text, models.DT_FORMAT)
    except ValueError:
        await bot.edit_message_text(
            "Невірний формат. Спробуйте ще раз\nВведіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
            msg.from_user.id,
            state_data["msg_id"],
            reply_markup=gen_cancel(purge_action.new(purge.id, "schedule"))
        )
        return
    await state.set_state(None)
    purges_db.update(purge)
    await open_purge_menu(msg.from_user.id, purge.id, state_data["msg_id"])


@dp.callback_query_handler(purge_action.filter(action="run"))
async def run(cb: CallbackQuery, callback_data: dict):
    purge = purges_db.get(int(callback_data["id"]))
    bot_dc = bots_db.get(purge.bot)
    purges_db.delete(purge.id)
    await cb.message.answer(
        "Вам прийде повідомлення після закінчення розсилки",
        reply_markup=gen_ok(bot_action.new(
            bot_dc.id,
            "purges"
        ))
    )
    try:
        await cb.message.delete()
    except MessageCantBeDeleted:
        pass
    cleared_num, error_num = await gig.clean(manager.bot_dict[bot_dc.token][0], purge)
    await cb.message.answer(
        f"Чистка {hex(purge.id*1234)} закінчена\nОчищено: {cleared_num}\nПомилка:{error_num}",
        reply_markup=gen_ok("hide")
    )

