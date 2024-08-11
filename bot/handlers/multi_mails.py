from bot.misc import *
from bot.keyboards import multi_mails as kb
from bot.keyboards import bot_action, multi_mail_action, gen_cancel, gen_ok, gen_confirmation
from datetime import datetime
from .mails import initiate_ubot_file


async def safe_get_multi_mail(uid: int, multi_mail_id: int, cb_id: int | None = None) -> models.MultiMail | None:
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
        multi_mail = await multi_mails_db.get(multi_mail_id)
    except data_exc.RecordIsMissing:
        await alert()
        return None
    if multi_mail.active == 1:
        await alert()
        return None
    return multi_mail


@dp.callback_query_handler(lambda cb: cb.data == "multi_mails", state="*")
async def open_multi_mail_list(cb: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    multi_mails = await multi_mails_db.get_by(sender=cb.from_user.id, active=0, status=0, admin=0)
    await cb.message.answer(
        "📮Мультирозсилки",
        reply_markup=kb.gen_multi_mail_list(multi_mails)
    )
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.callback_query_handler(lambda cb: cb.data == "add_multi_mail")
async def add_multi_mail(cb: CallbackQuery, state: FSMContext):
    msg = await cb.message.answer(
        f"Надішліть текст, гіф, фото або відео з підписом.\nДинамічні змінні:\n\
<b>[any]\n[username]\n[first_name]\n[last_name]</b>",
        reply_markup=gen_cancel(
             "multi_mails"
        )
    )
    await state.set_state(states.InputStateGroup.multi_mail)
    await state.set_data({"msg_id": msg.message_id, "edit": None})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.callback_query_handler(multi_mail_action.filter(action="edit_multi_mail"))
async def edit_mail(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    multi_mail = await safe_get_multi_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not multi_mail:
        return
    msg = await cb.message.answer(
        "Надішліть текст, гіф, фото або відео з підписом.\nДинамічні змінні:\n\
<b>[any]\n[username]\n[first_name]\n[last_name]</b>",
        reply_markup=gen_cancel(
            callback_data=multi_mail_action.new(
                id=multi_mail.id,
                action="open_multi_mail_menu",
                extra_field=0
            )
        )
    )
    await state.set_state(states.InputStateGroup.multi_mail)
    await state.set_data({"msg_id": msg.message_id, "edit": multi_mail.id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


async def open_multi_mail_menu(uid: int, multi_mail_id: int, msg_id: int):
    multi_mail = await multi_mails_db.get(multi_mail_id)
    sched_text = "\n"
    if multi_mail.send_dt:
        sched_text += f"\n<i>🕑Заплановано на: {multi_mail.send_dt.strftime(models.DT_FORMAT)}</i>"
    if multi_mail.del_dt:
        sched_text += f"\n<i>🗑Видалення: {multi_mail.del_dt.strftime(models.DT_FORMAT)}</i>"
    multi_mail_text_content = multi_mail.text if multi_mail.text else ""
    multi_mail_text_content += sched_text
    if multi_mail.photo:
        file = file_manager.get_file(multi_mail.photo)
        await bot.send_photo(
            uid,
            file,
            caption=multi_mail_text_content,
            reply_markup=kb.gen_multi_mail_menu(multi_mail)
        )
    elif multi_mail.video:
        file = file_manager.get_file(multi_mail.video)
        await bot.send_video(
            uid,
            file,
            caption=multi_mail_text_content,
            reply_markup=kb.gen_multi_mail_menu(multi_mail)
        )
    elif multi_mail.gif:
        file = file_manager.get_file(multi_mail.gif)
        await bot.send_animation(
            uid,
            file,
            caption=multi_mail_text_content,
            reply_markup=kb.gen_multi_mail_menu(multi_mail)
        )
    elif multi_mail.text:
        await bot.send_message(
            uid,
            multi_mail_text_content,
            reply_markup=kb.gen_multi_mail_menu(multi_mail)
        )
    await safe_del_msg(uid, msg_id)


@dp.callback_query_handler(multi_mail_action.filter(action="open_multi_mail_menu"), state="*")
async def open_multi_mail_menu_cb(cb: CallbackQuery, callback_data: dict):
    multi_mail = await safe_get_multi_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not multi_mail:
        return
    await open_multi_mail_menu(cb.from_user.id, int(callback_data["id"]), cb.message.message_id)


async def multi_mail_input(
        msg: Message, state: FSMContext, text: str = None, photo: str = None, video: str = None, gif: str = None
):
    state_data = await state.get_data()
    if state_data["edit"]:
        multi_mail = await multi_mails_db.get(state_data["edit"])
        multi_mail.text = text
        multi_mail.photo = photo
        multi_mail.video = video
        multi_mail.gif = gif
        await multi_mails_db.update(multi_mail)
    else:
        multi_mail = models.MultiMail(
            _id=0,
            sender=msg.from_user.id,
            text=text,
            photo=photo,
            video=video,
            gif=gif
        )
        await multi_mails_db.add(multi_mail)
    if not multi_mail.admin:
        await select_bots(msg.from_user.id, multi_mail.id, state_data["msg_id"])
    else:
        create_task(open_multi_mail_menu(msg.from_user.id, multi_mail.id, state_data["msg_id"]))
    await state.set_state(None)
    await msg.delete()


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.multi_mail)
async def multi_mail_input_text(msg: Message, state: FSMContext):
    await multi_mail_input(
        msg,
        state,
        text=msg.parse_entities(as_html=True) if msg.text else None
    )


@dp.message_handler(content_types=ContentTypes.PHOTO, state=states.InputStateGroup.multi_mail)
async def multi_mail_input_photo(msg: Message, state: FSMContext):
    filename = await file_manager.download_file(bot, f"admin{msg.from_user.id}", msg.photo[-1].file_id)
    await multi_mail_input(
        msg,
        state,
        text=msg.parse_entities(as_html=True) if msg.caption else None,
        photo=filename
    )


@dp.message_handler(content_types=ContentTypes.VIDEO, state=states.InputStateGroup.multi_mail)
async def multi_mail_input_video(msg: Message, state: FSMContext):
    filename = await file_manager.download_file(bot, f"admin{msg.from_user.id}", msg.video.file_id)
    await multi_mail_input(
        msg,
        state,
        text=msg.parse_entities(as_html=True) if msg.caption else None,
        video=filename
    )


@dp.message_handler(content_types=ContentTypes.ANIMATION, state=states.InputStateGroup.multi_mail)
async def multi_mail_input_gif(msg: Message, state: FSMContext):
    filename = await file_manager.download_file(bot, f"admin{msg.from_user.id}", msg.animation.file_id)
    await multi_mail_input(
        msg,
        state,
        text=msg.parse_entities(as_html=True) if msg.caption else None,
        gif=filename
    )


async def select_bots(uid: int, multi_mail_id: int, msg_id: int):
    multi_mail = await multi_mails_db.get(multi_mail_id)
    bots_dc = await bots_db.get_by(admin=uid)
    await bot.send_message(
        uid,
        "Виберіть ботів",
        reply_markup=kb.gen_bot_select_menu(multi_mail, bots_dc)
    )
    await safe_del_msg(uid, msg_id)


@dp.callback_query_handler(multi_mail_action.filter(action="bots_select"))
async def select_bots_cb(cb: CallbackQuery, callback_data: dict):
    await select_bots(cb.from_user.id, int(callback_data["id"]), cb.message.message_id)


@dp.callback_query_handler(multi_mail_action.filter(action="attach_bot"))
async def attach_bot(cb: CallbackQuery, callback_data: dict):
    multi_mail = await multi_mails_db.get(int(callback_data["id"]))
    bot_id = int(callback_data["extra_field"])
    bot_dc = await bots_db.get(bot_id)
    if bot_dc.premium <= 0:
        await cb.answer("⭐️Лише для преміум ботів")
        return
    if bot_id not in multi_mail.bots:
        multi_mail.bots.append(bot_id)
        await multi_mails_db.update(multi_mail)
    await select_bots(cb.from_user.id, multi_mail.id, cb.message.message_id)


@dp.callback_query_handler(multi_mail_action.filter(action="detach_bot"))
async def detach_bot(cb: CallbackQuery, callback_data: dict):
    multi_mail = await multi_mails_db.get(int(callback_data["id"]))
    bot_id = int(callback_data["extra_field"])
    if bot_id in multi_mail.bots:
        multi_mail.bots.remove(bot_id)
        await multi_mails_db.update(multi_mail)
    await select_bots(cb.from_user.id, multi_mail.id, cb.message.message_id)


@dp.callback_query_handler(multi_mail_action.filter(action="add_buttons"))
async def add_buttons(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    multi_mail = await safe_get_multi_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not multi_mail:
        return
    msg = await cb.message.answer(
        "Щоб додати кнопки-посилання надішліть список у форматі\n\
<b>text_1 - link_1 | text_2 - link_2\ntext_3 - link_3\n...</b>",
        reply_markup=gen_cancel(
            multi_mail_action.new(
                id=callback_data["id"],
                action="open_multi_mail_menu",
                extra_field=0
            )
        )
    )
    await safe_del_msg(cb.from_user.id, cb.message.message_id)
    await state.set_state(states.InputStateGroup.multi_mail_buttons)
    await state.set_data({"msg_id": msg.message_id, "mail_id": callback_data["id"]})


def button_input_filter(msg: Message) -> bool:
    try:
        models.deserialize_buttons(msg.text)
        return True
    except ValueError:
        return False


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.multi_mail_buttons)
async def multi_mail_buttons_input(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    multi_mail = await multi_mails_db.get(state_data["mail_id"])
    await msg.delete()
    try:
        input_buttons = models.deserialize_buttons(msg.text)
    except ValueError:
        await safe_edit_message(
            "❗️Невірний формат. Cпробуйте ще раз\nЩоб додати кнопки-посилання надішліть список у форматі\n\
<i><b>text_1 - link_1 | text_2 - link_2\ntext_3 - link_3\n...</b></i>",
            msg.from_user.id,
            state_data["msg_id"],
            reply_markup=gen_cancel(
                multi_mail_action.new(
                    id=multi_mail.id,
                    action="open_multi_mail_menu",
                    extra_field=0
                )
            )
        )
        return
    multi_mail.buttons = input_buttons
    await multi_mails_db.update(multi_mail)
    await state.set_state(None)
    await open_multi_mail_menu(msg.from_user.id, multi_mail.id, state_data["msg_id"])


@dp.callback_query_handler(multi_mail_action.filter(action="delete_mail"))
async def delete_mail(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    multi_mail = await safe_get_multi_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not multi_mail:
        return
    await multi_mails_db.delete(multi_mail.id)
    await safe_del_msg(multi_mail.sender, cb.message.message_id)
    if multi_mail.admin:
        await bot.send_message(
            multi_mail.sender,
            "🕳Адмінська розсилка була видалена",
            reply_markup=gen_ok("admin_mails_list")
        )
    else:
        await bot.send_message(
            multi_mail.sender,
            "🕳Мультирозсилка була видалена",
            reply_markup=gen_ok("multi_mails"))


async def multi_mail_schedule_menu(uid: int, multi_mail_id: int, msg_id: int):
    multi_mail = await multi_mails_db.get(multi_mail_id)
    await bot.send_message(
        uid,
        f"<i>📩Час надсилання: {multi_mail.send_dt.strftime(models.DT_FORMAT) if multi_mail.send_dt else 'немає'}\n\
♻️Час видалення: {multi_mail.del_dt.strftime(models.DT_FORMAT) if multi_mail.del_dt else 'немає'}</i>",
        reply_markup=kb.gen_schedule_menu(multi_mail)
    )
    await safe_del_msg(uid, msg_id)


@dp.callback_query_handler(multi_mail_action.filter(action="schedule"), state="*")
async def multi_mail_schedule_menu_cb(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    multi_mail = await safe_get_multi_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not multi_mail:
        return
    await state.set_state(None)
    await multi_mail_schedule_menu(cb.from_user.id, int(callback_data["id"]), cb.message.message_id)


@dp.callback_query_handler(multi_mail_action.filter(action="edit_send_dt"))
async def edit_send_dt(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    multi_mail = await safe_get_multi_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not multi_mail:
        return
    msg = await cb.message.answer(
        "Введіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
        reply_markup=kb.gen_cancel_schedule_menu(multi_mail)
    )
    await state.set_state(states.InputStateGroup.multi_mail_send_dt)
    await state.set_data({"mail_id": int(callback_data["id"]), "msg_id": msg.message_id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.multi_mail_send_dt)
async def edit_send_dt(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    multi_mail = await safe_get_multi_mail(msg.from_user.id, state_data["mail_id"])
    if not multi_mail:
        return
    await safe_del_msg(msg.from_user.id, msg.message_id)
    try:
        input_dt = datetime.strptime(msg.text, models.DT_FORMAT)
    except ValueError:
        await safe_edit_message(
            "❗️Невірний формат. Спробуйте ще раз\n\n\
Введіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
            msg.from_user.id,
            state_data["msg_id"],
            reply_markup=kb.gen_cancel_schedule_menu(multi_mail)
        )
        return
    if tz.localize(input_dt) < datetime.now(tz=tz):
        await safe_edit_message(
            "❗️Введена дата не може бути у минулому. Спробуйте ще раз\n\n\
Введіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
            msg.from_user.id,
            state_data["msg_id"],
            reply_markup=kb.gen_cancel_schedule_menu(multi_mail)
        )
        return
    if multi_mail.del_dt and (multi_mail.del_dt - input_dt).total_seconds() / 3600 > 47.75:
        await safe_edit_message(
            "❗️Різниця між часом надсилання та часом автовидалення не може перевищувати 48 годин. Спробуйте ще раз\n\n\
Введіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
            msg.from_user.id,
            state_data["msg_id"],
            reply_markup=kb.gen_cancel_schedule_menu(multi_mail)
        )
        return
    multi_mail.send_dt = input_dt
    await state.set_state(None)
    await multi_mails_db.update(multi_mail)
    await multi_mail_schedule_menu(msg.from_user.id, multi_mail.id, state_data["msg_id"])


@dp.callback_query_handler(multi_mail_action.filter(action="del_send_dt"))
async def del_send_dt(cb: CallbackQuery, callback_data: dict):
    multi_mail = await safe_get_multi_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not multi_mail:
        return
    multi_mail.send_dt = None
    await multi_mails_db.update(multi_mail)
    await multi_mail_schedule_menu(cb.from_user.id, multi_mail.id, cb.message.message_id)


@dp.callback_query_handler(multi_mail_action.filter(action="edit_del_dt"))
async def edit_del_dt(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    multi_mail = await safe_get_multi_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not multi_mail:
        return
    msg = await cb.message.answer(
        "Введіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
        reply_markup=kb.gen_cancel_schedule_menu(multi_mail)
    )
    await state.set_state(states.InputStateGroup.multi_mail_del_dt)
    await state.set_data({"mail_id": int(callback_data["id"]), "msg_id": msg.message_id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.multi_mail_del_dt)
async def edit_del_dt(msg: Message, state: FSMContext):
    await safe_del_msg(msg.from_user.id, msg.message_id)
    state_data = await state.get_data()
    multi_mail = await safe_get_multi_mail(msg.from_user.id, state_data["mail_id"])
    if not multi_mail:
        return
    try:
        input_dt = datetime.strptime(msg.text, models.DT_FORMAT)
    except ValueError:
        await safe_edit_message(
            "❗️Невірний формат. Спробуйте ще раз\n\nВведіть дату та час у форматі <i>[H:M d.m.Y]</i>\n\
Приклад: <i>16:20 12.05.2023</i>",
            msg.from_user.id,
            state_data["msg_id"],
            reply_markup=kb.gen_cancel_schedule_menu(multi_mail)
        )
        return
    if tz.localize(input_dt) < datetime.now(tz=tz):
        await safe_edit_message(
            "❗️Введена дата не може бути у минулому. Спробуйте ще раз\n\n\
Введіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
            msg.from_user.id,
            state_data["msg_id"],
            reply_markup=kb.gen_cancel_schedule_menu(multi_mail)
        )
        return
    if multi_mail.send_dt and (input_dt - multi_mail.send_dt).total_seconds() / 3600 > 47.75:
        await safe_edit_message(
            "❗️Різниця між часом надсилання та часом автовидалення не може перевищувати 48 годин. Спробуйте ще раз\n\n\
Введіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
            msg.from_user.id,
            state_data["msg_id"],
            reply_markup=kb.gen_cancel_schedule_menu(multi_mail)
        )
        return
    multi_mail.del_dt = input_dt
    await multi_mails_db.update(multi_mail)
    await state.set_state(None)
    await multi_mail_schedule_menu(msg.from_user.id, multi_mail.id, state_data["msg_id"])


@dp.callback_query_handler(multi_mail_action.filter(action="del_del_dt"))
async def del_del_dt(cb: CallbackQuery, callback_data: dict):
    multi_mail = await safe_get_multi_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not multi_mail:
        return
    multi_mail.del_dt = None
    await multi_mails_db.update(multi_mail)
    await multi_mail_schedule_menu(cb.from_user.id, multi_mail.id, cb.message.message_id)


@dp.callback_query_handler(multi_mail_action.filter(action="sendout"))
async def sendout(cb: CallbackQuery, callback_data: dict):
    multi_mail = await safe_get_multi_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not multi_mail:
        return
    if multi_mail.del_dt and (tz.localize(multi_mail.del_dt) - datetime.now(tz=tz)).total_seconds() / 3600 > 47.75:
        await cb.answer(
            "❗️Різниця між часом надсилання та часом автовидалення не може перевищувати 48 годин.\n\
Змініть час автовидалення автовидалення",
            show_alert=True
        )
        return
    await cb.message.answer(
        "Ви впевнені, що хочете запустити розсилку?",
        reply_markup=gen_confirmation(
            multi_mail_action.new(
                id=multi_mail.id,
                action="confirm_sendout",
                extra_field=0
            ),
            multi_mail_action.new(
                id=multi_mail.id,
                action="open_multi_mail_menu",
                extra_field=0
            )
        )
    )
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


async def run_multi_mail(multi_mail: models.MultiMail, uid: int):
    if multi_mail.photo:
        filename = multi_mail.photo
    elif multi_mail.video:
        filename = multi_mail.video
    elif multi_mail.gif:
        filename = multi_mail.gif
    else:
        filename = None
    bots_dc = [await bots_db.get(id) for id in multi_mail.bots]
    for bot_dc in bots_dc:
        mail = models.Mail(
            0,
            sender=uid,
            bot=bot_dc.id,
            active=False,
            text=multi_mail.text,
            photo=multi_mail.photo,
            video=multi_mail.video,
            gif=multi_mail.gif,
            buttons=models.serialize_buttons(multi_mail.buttons),
            del_dt=datetime.strftime(multi_mail.del_dt, models.DT_FORMAT) if multi_mail.del_dt else None,
            multi_mail=multi_mail.id
        )

        if filename:
            try:
                file_id = await initiate_ubot_file(mail)
            except (ChatNotFound, Unauthorized, KeyError):
                multi_mail.bots.remove(bot_dc.id)
                continue
            mail.file_id = file_id
        await mails_db.add(mail)
        if mail.del_dt:
            purge = models.Purge(0, sender=mail.sender, bot=mail.bot,
                                 sched_dt=datetime.strftime(mail.del_dt, models.DT_FORMAT), mail_id=mail.id)
            await purges_db.add(purge)
        create_task(gig.enqueue_mail(mail))
    multi_mail.active = 1
    await multi_mails_db.update(multi_mail)
    if multi_mail.admin:
        queue_msg = f"🚀Адмінська розсилка {gen_hex_caption(multi_mail.id)} була запущена. Вам прийде повідомлення після її закінчення"
    else:
        queue_msg = f"🚀Мультирозсилка {gen_hex_caption(multi_mail.id)} була запущена. Вам прийде повідомлення після її закінчення"
    await bot.send_message(multi_mail.sender, queue_msg, reply_markup=gen_ok("hide", "Ого їбане зараз" if multi_mail.admin else "OK"))


@dp.callback_query_handler(multi_mail_action.filter(action="confirm_sendout"))
async def confirm_sendout(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    multi_mail = await safe_get_multi_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not multi_mail:
        return
    if not multi_mail.admin:
        await open_multi_mail_list(cb, state)
    await run_multi_mail(multi_mail, cb.from_user.id)
    await safe_del_msg(cb.from_user.id, cb.message.message_id)
