from bot.misc import *
from bot.keyboards import mails as kb
from bot.keyboards import bot_action, mail_action, gen_cancel, gen_ok
from datetime import datetime


async def safe_get_mail(uid: int, mail_id: int, cb_id: int | None = None) -> models.Mail | None:
    try:
        mail = mails_db.get(mail_id)
        return mail
    except data_exc.RecordIsMissing:
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
        return None


@dp.callback_query_handler(bot_action.filter(action="mails"), state="*")
async def open_mail_list(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.set_state(None)
    bot_dc = bots_db.get(int(callback_data["id"]))
    mails = mails_db.get_by(bot=int(callback_data["id"]))
    await cb.message.answer(
        "{text6}\nРозсилки:",
        reply_markup=kb.gen_mail_list(bot_dc, mails)
    )
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.callback_query_handler(bot_action.filter(action="add_mail"))
async def add_mail(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    bot_dc = bots_db.get(int(callback_data["id"]))
    msg = await cb.message.answer(
        "Надішліть текст, гіф, фото або відео з підписом",
        reply_markup=gen_cancel(
            bot_action.new(
                id=bot_dc.id,
                action="mails"
            )
        )
    )
    await state.set_state(states.InputStateGroup.mail)
    await state.set_data({"msg_id": msg.message_id, "bot_id": bot_dc.id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


async def open_mail_menu(uid: int, mail_id: int, msg_id: int):
    mail = mails_db.get(mail_id)
    if mail.send_dt != None:
        if mail.text == None:
            mail.text = ""
        mail.text += f"\n\n<i>Заплановано на: {mail.send_dt.strftime(models.DT_FORMAT)}</i>"
    bot_dc = bots_db.get(mail.bot)
    if mail.photo:
        file = await file_manager.get_file(mail.photo)
        await bot.send_photo(
            uid,
            file,
            caption=mail.text,
            reply_markup=kb.gen_mail_menu(bot_dc, mail)
        )
    elif mail.video:
        file = await file_manager.get_file(mail.video)
        await bot.send_video(
            uid,
            file,
            caption=mail.text,
            reply_markup=kb.gen_mail_menu(bot_dc, mail)
        )
    elif mail.gif:
        file = await file_manager.get_file(mail.gif)
        await bot.send_animation(
            uid,
            file,
            caption=mail.text,
            reply_markup=kb.gen_mail_menu(bot_dc, mail)
        )
    elif mail.text:
        await bot.send_message(
            uid,
            mail.text,
            reply_markup=kb.gen_mail_menu(bot_dc, mail)
        )
    await safe_del_msg(uid, msg_id)


@dp.callback_query_handler(mail_action.filter(action="open_mail_menu"), state="*")
async def open_mail_menu_cb(cb: CallbackQuery, callback_data: dict):
    mail = await safe_get_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not mail:
        return
    await open_mail_menu(cb.from_user.id, int(callback_data["id"]), cb.message.message_id)


@dp.callback_query_handler(bot_action.filter(action="add_mail"))
async def add_mail(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    bot_dc = bots_db.get(int(callback_data["id"]))
    msg = await cb.message.answer(
        "Надішліть текст, гіф, фото або відео з підписом",
        reply_markup=gen_cancel(
            bot_action.new(
                id=bot_dc.id,
                action="mails"
            )
        )
    )
    await state.set_state(states.InputStateGroup.mail)
    await state.set_data({"msg_id": msg.message_id, "bot_id": bot_dc.id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.mail)
async def mail_input_text(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    mail = models.Mail(
        _id=0,
        bot=state_data["bot_id"],
        text=msg.text
    )
    mails_db.add(mail)
    await open_mail_menu(msg.from_user.id, mail.id, state_data["msg_id"])
    await state.set_state(None)
    await msg.delete()


@dp.message_handler(content_types=ContentTypes.PHOTO, state=states.InputStateGroup.mail)
async def mail_input_photo(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    mail = models.Mail(
        _id=0,
        bot=state_data["bot_id"],
        text=msg.text,
        photo=await file_manager.download_file(bot, state_data["bot_id"], msg.photo[-1].file_id)
    )
    mails_db.add(mail)
    await open_mail_menu(msg.from_user.id, mail.id, state_data["msg_id"])
    await state.set_state(None)
    await msg.delete()


@dp.message_handler(content_types=ContentTypes.VIDEO, state=states.InputStateGroup.mail)
async def mail_input_video(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    mail = models.Mail(
        _id=0,
        bot=state_data["bot_id"],
        text=msg.text,
        video=await file_manager.download_file(bot, state_data["bot_id"], msg.video.file_id)
    )
    mails_db.add(mail)
    await open_mail_menu(msg.from_user.id, mail.id, state_data["msg_id"])
    await state.set_state(None)
    await msg.delete()


@dp.message_handler(content_types=ContentTypes.ANIMATION, state=states.InputStateGroup.mail)
async def mail_input_gif(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    mail = models.Mail(
        _id=0,
        bot=state_data["bot_id"],
        text=msg.text,
        gif=await file_manager.download_file(bot, state_data["bot_id"], msg.animation.file_id)
    )
    mails_db.add(mail)
    await open_mail_menu(msg.from_user.id, mail.id, state_data["msg_id"])
    await state.set_state(None)
    await msg.delete()


@dp.callback_query_handler(mail_action.filter(action="add_buttons"))
async def add_buttons(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    mail = await safe_get_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not mail:
        return
    msg = await cb.message.answer(
        "Щоб додати кнопки-посилання надішліть список у форматі\nпідпис1 - посилання1\nпідпис2 - посилання2\n...",
        reply_markup=gen_cancel(
            mail_action.new(
                id=callback_data["id"],
                action="open_mail_menu"
            )
        )
    )
    await safe_del_msg(cb.from_user.id, cb.message.message_id)
    await state.set_state(states.InputStateGroup.mail_buttons)
    await state.set_data({"msg_id": msg.message_id, "mail_id": callback_data["id"]})


def button_input_filter(msg: Message) -> bool:
    try:
        models.deserialize_buttons(msg.text)
        return True
    except ValueError:
        return False


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.mail_buttons)
async def mail_buttons_input(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    mail = mails_db.get(state_data["mail_id"])
    await msg.delete()
    try:
        mail.buttons = models.deserialize_buttons(msg.text)
    except ValueError:
        await bot.edit_message_text(
            "Невірний формат. Cпробуйте ще раз\nЩоб додати кнопки-посилання надішліть список у форматі\nпідпис1 - посилання1\nпідпис2 - посилання2\n...",
            msg.from_user.id,
            state_data["msg_id"],
            reply_markup=gen_cancel(
                mail_action.new(
                    id=mail.id,
                    action="open_mail_menu"
                )
            )
        )
        return
    mails_db.update(mail)
    await state.set_state(None)
    await open_mail_menu(msg.from_user.id, mail.id, state_data["msg_id"])


@dp.callback_query_handler(mail_action.filter(action="delete_mail"))
async def delete_mail(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    mail = await safe_get_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not mail:
        return
    mails_db.delete(mail.id)
    await open_mail_list(cb, {"id": mail.bot}, state)


async def mail_schedule_menu(uid: int, mail_id: int, msg_id: int):
    mail = mails_db.get(mail_id)
    await bot.send_message(
        uid,
        f"<i>📩Час надсилання: {mail.send_dt.strftime(models.DT_FORMAT) if mail.send_dt else 'немає'}\n\
♻️Час видалення: {mail.del_dt.strftime(models.DT_FORMAT) if mail.del_dt else 'немає'}</i>",
        reply_markup=kb.gen_schedule_menu(mail)
    )
    await safe_del_msg(uid, msg_id)


@dp.callback_query_handler(mail_action.filter(action="schedule"), state="*")
async def mail_schedule_menu_cb(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    mail = await safe_get_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not mail:
        return
    await state.set_state(None)
    await mail_schedule_menu(cb.from_user.id, int(callback_data["id"]), cb.message.message_id)


@dp.callback_query_handler(mail_action.filter(action="edit_send_dt"))
async def edit_send_dt(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    mail = await safe_get_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not mail:
        return
    msg = await cb.message.answer(
        "Введіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
        reply_markup=gen_cancel(mail_action.new(callback_data["id"], "schedule"))
    )
    await state.set_state(states.InputStateGroup.mail_send_dt)
    await state.set_data({"mail_id": int(callback_data["id"]), "msg_id": msg.message_id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.mail_send_dt)
async def edit_send_dt(msg: Message, state: FSMContext): 
    state_data = await state.get_data()
    mail = await safe_get_mail(msg.from_user.id, state_data["mail_id"])
    try:
        await msg.delete()
    except MessageToDeleteNotFound:
        pass
    try:
        if ukraine_tz.localize(datetime.strptime(msg.text, models.DT_FORMAT)) > datetime.now(tz=timezone('Europe/Kiev')):
            mail.del_dt = datetime.strptime(msg.text, models.DT_FORMAT)
        else:
            await bot.edit_message_text(
            "Дата розсилки не може бути у минулому. Спробуйте ще раз\nВведіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
            msg.from_user.id,
            state_data["msg_id"],
            reply_markup=gen_cancel(mail_action.new(mail.id, "schedule"))
        )
            return
    except ValueError:
        await bot.edit_message_text(
            "Невірний формат. Спробуйте ще раз\nВведіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
            msg.from_user.id,
            state_data["msg_id"],
            reply_markup=gen_cancel(mail_action.new(mail.id, "schedule"))
        )
        return
    await state.set_state(None)
    mails_db.update(mail)
    await mail_schedule_menu(msg.from_user.id, mail.id, state_data["msg_id"])


@dp.callback_query_handler(mail_action.filter(action="del_send_dt"))
async def del_send_dt(cb: CallbackQuery, callback_data: dict):
    mail = await safe_get_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not mail:
        return
    mail.send_dt = None
    mails_db.update(mail)
    await mail_schedule_menu(cb.from_user.id, mail.id, cb.message.message_id)


@dp.callback_query_handler(mail_action.filter(action="edit_del_dt"))
async def edit_del_dt(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    mail = await safe_get_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not mail:
        return
    bot_dc = bots_db.get(mail.bot)
    if bot_dc.premium <= 0:
        await cb.answer("⭐️Лише для преміум ботів")
        return
    msg = await cb.message.answer(
        "Введіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
        reply_markup=gen_cancel(mail_action.new(callback_data["id"], "schedule"))
    )
    await state.set_state(states.InputStateGroup.mail_del_dt)
    await state.set_data({"mail_id": int(callback_data["id"]), "msg_id": msg.message_id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.mail_del_dt)
async def edit_del_dt(msg: Message, state: FSMContext):
    await msg.delete()
    state_data = await state.get_data()
    mail = mails_db.get(state_data["mail_id"])
    await msg.delete()
    try:
        if ukraine_tz.localize(datetime.strptime(msg.text, models.DT_FORMAT)) > datetime.now(tz=timezone('Europe/Kiev')):
            mail.del_dt = datetime.strptime(msg.text, models.DT_FORMAT)
        else:
            await bot.edit_message_text(
            "Дата розсилки не може бути у минулому. Спробуйте ще раз\nВведіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
            msg.from_user.id,
            state_data["msg_id"],
            reply_markup=gen_cancel(mail_action.new(mail.id, "schedule"))
        )
            return
    except ValueError:
        await bot.edit_message_text(
            "Невірний формат. Спробуйте ще раз\nВведіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
            msg.from_user.id,
            state_data["msg_id"],
            reply_markup=gen_cancel(mail_action.new(mail.id, "schedule"))
        )
        return
    await state.set_state(None)
    mails_db.update(mail)
    await mail_schedule_menu(msg.from_user.id, mail.id, state_data["msg_id"])


@dp.callback_query_handler(mail_action.filter(action="del_del_dt"))
async def del_del_dt(cb: CallbackQuery, callback_data: dict):
    mail = await safe_get_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not mail:
        return
    mail.del_dt = None
    mails_db.update(mail)
    await mail_schedule_menu(cb.from_user.id, mail.id, cb.message.message_id)


@dp.callback_query_handler(mail_action.filter(action="sendout"))
async def sendout(cb: CallbackQuery, callback_data: dict):
    mail = await safe_get_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not mail:
        return
    bot_dc = bots_db.get(mail.bot)
    mails_db.delete(mail.id)
    await cb.message.answer(
        "Вам прийде повідомлення після закінчення розсилки",
        reply_markup=gen_ok(bot_action.new(
            bot_dc.id,
            "mails"
        ))
    )
    await safe_del_msg(cb.from_user.id, cb.message.message_id)
    sent_num, blocked_num, error_num = await gig.send_mail(manager.bot_dict[bot_dc.token][0], mail)
    await cb.message.answer(
        f"Розсилка {hex(mail.id*1234)} закінчена\nНадіслано: {sent_num}\nЗаблоковано:{blocked_num}\nПомилка:{error_num}",
        reply_markup=gen_ok("hide")
    )
