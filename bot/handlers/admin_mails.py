import bot.handlers.settings
from bot.misc import *
from bot.keyboards import admin_mails as kb
from bot.keyboards import admin_mail_action, gen_cancel, gen_ok, gen_confirmation


async def safe_get_admin_mail(uid: int, mail_id: int, cb_id: int | None = None) -> models.AdminMail | None:
    try:
        admin_mail = await admin_mails_db.get(mail_id)
        return admin_mail
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
                reply_markup=gen_ok("admin", "↩️Адмін панель")
            )
        return None


@dp.callback_query_handler(admin_mail_action.filter(action="admin_mails_list"), state="*")
async def menu_admin_mails(cb: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    admin_mails = await admin_mails_db.get_by(status=0)
    await cb.message.answer(
        "<i>💡В цьому меню, можна створити, редагувати та запускати розсилки у всі боти. \
</i>\n\n\
<b>📩Розсилки:</b>",
        reply_markup=kb.gen_admin_mail_list(admin_mails)
    )
    await cb.message.delete()


@dp.callback_query_handler(admin_mail_action.filter(action="add_mail"))
async def add_mail(cb: CallbackQuery, state: FSMContext):
    msg = await cb.message.answer(
        "Надішліть текст, гіф, фото або відео з підписом.\nДинамічні змінні:\n<b>[any]\n[username]\n[first_name]\n[last_name]</b>",
        reply_markup=gen_cancel(admin_mail_action.new(
            id=0,
            action="admin_mails_list"
        )
        )
    )
    await state.set_state(states.InputStateGroup.admin_mail)
    await state.set_data({"msg_id": msg.message_id, "bot_id": msg.bot.id, "edit": None})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.callback_query_handler(admin_mail_action.filter(action="edit_admin_mail"))
async def edit_mail(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    admin_mail = await safe_get_admin_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not admin_mail:
        return
    msg = await cb.message.answer(
        "Надішліть текст, гіф, фото або відео з підписом.\nДинамічні змінні:\n<b>[any]\n[username]\n[first_name]\n[last_name]</b>",
        reply_markup=gen_cancel(
            callback_data=admin_mail_action.new(
                id=admin_mail.id,
                action="admin_mails_list"
            )
        )
    )
    await state.set_state(states.InputStateGroup.admin_mail)
    await state.set_data({"msg_id": msg.message_id, "bot_id": msg.bot.id, "edit": admin_mail.id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


async def open_admin_mail_menu(uid: int, mail_id: int, msg_id: int):
    admin_mail = await admin_mails_db.get(mail_id)
    sched_text = "\n"
    if admin_mail.send_dt:
        sched_text += f"\n<i>🕑Заплановано на: {admin_mail.send_dt.strftime(models.DT_FORMAT)}</i>"
    admin_mail_text_content = admin_mail.text if admin_mail.text else ""
    admin_mail_text_content += sched_text
    if admin_mail.photo:
        file = file_manager.get_file(admin_mail.photo)
        await bot.send_photo(
            uid,
            file,
            caption=admin_mail_text_content,
            reply_markup=kb.gen_admin_mail_menu(admin_mail)
        )
    elif admin_mail.video:
        file = file_manager.get_file(admin_mail.video)
        await bot.send_video(
            uid,
            file,
            caption=admin_mail_text_content,
            reply_markup=kb.gen_admin_mail_menu(admin_mail)
        )
    elif admin_mail.gif:
        file = file_manager.get_file(admin_mail.gif)
        await bot.send_animation(
            uid,
            file,
            caption=admin_mail_text_content,
            reply_markup=kb.gen_admin_mail_menu(admin_mail)
        )
    elif admin_mail.text:
        await bot.send_message(
            uid,
            admin_mail_text_content,
            reply_markup=kb.gen_admin_mail_menu(admin_mail)
        )
    await safe_del_msg(uid, msg_id)


@dp.callback_query_handler(admin_mail_action.filter(action="open_admin_mail_menu"), state="*")
async def open_admin_mail_menu_cb(cb: CallbackQuery, callback_data: dict):
    mail = await safe_get_admin_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not mail:
        return
    await open_admin_mail_menu(cb.from_user.id, int(callback_data["id"]), cb.message.message_id)


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.admin_mail)
async def admin_mail_input_text(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    if state_data["edit"]:
        admin_mail = await admin_mails_db.get(state_data["edit"])
        admin_mail.text = msg.parse_entities(as_html=True) if msg.text else None
        admin_mail.photo = None
        admin_mail.video = None
        admin_mail.gif = None
        await admin_mails_db.update(admin_mail)
    else:
        admin_mail = models.AdminMail(
            _id=0,
            text=msg.parse_entities(as_html=True) if msg.text else None,
            sender=msg.from_user.id
        )
        await admin_mails_db.add(admin_mail)
    await open_admin_mail_menu(msg.from_user.id, admin_mail.id, state_data["msg_id"])
    await state.set_state(None)
    await msg.delete()


@dp.message_handler(content_types=ContentTypes.PHOTO, state=states.InputStateGroup.admin_mail)
async def mail_input_photo(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    filename = await file_manager.download_file(bot, state_data["bot_id"], msg.photo[-1].file_id)
    if state_data["edit"]:
        admin_mail = await admin_mails_db.get(state_data["edit"])
        admin_mail.text = msg.parse_entities(as_html=True) if msg.caption else None
        admin_mail.photo = filename
        admin_mail.video = None
        admin_mail.gif = None
        await admin_mails_db.update(admin_mail)
    else:
        admin_mail = models.AdminMail(
            _id=0,
            text=msg.parse_entities(as_html=True) if msg.caption else None,
            photo=filename,
            sender=msg.from_user.id
        )
        await admin_mails_db.add(admin_mail)
    await open_admin_mail_menu(msg.from_user.id, admin_mail.id, state_data["msg_id"])
    await state.set_state(None)
    await msg.delete()


@dp.message_handler(content_types=ContentTypes.VIDEO, state=states.InputStateGroup.admin_mail)
async def mail_input_video(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    filename = await file_manager.download_file(bot, state_data["bot_id"], msg.video.file_id)
    if state_data["edit"]:
        admin_mail = await admin_mails_db.get(state_data["edit"])
        admin_mail.text = msg.parse_entities(as_html=True) if msg.caption else None
        admin_mail.photo = None
        admin_mail.video = filename
        admin_mail.gif = None
        await admin_mails_db.update(admin_mail)
    else:
        admin_mail = models.AdminMail(
            _id=0,
            text=msg.parse_entities(as_html=True) if msg.caption else None,
            video=filename,
            sender=msg.from_user.id
        )
        await admin_mails_db.add(admin_mail)
    await open_admin_mail_menu(msg.from_user.id, admin_mail.id, state_data["msg_id"])
    await state.set_state(None)
    await msg.delete()


@dp.message_handler(content_types=ContentTypes.ANIMATION, state=states.InputStateGroup.admin_mail)
async def mail_input_gif(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    filename = await file_manager.download_file(bot, state_data["bot_id"], msg.animation.file_id)
    if state_data["edit"]:
        admin_mail = await admin_mails_db.get(state_data["edit"])
        admin_mail.text = msg.parse_entities(as_html=True) if msg.caption else None
        admin_mail.photo = None
        admin_mail.video = None
        admin_mail.gif = filename
        await admin_mails_db.update(admin_mail)
    else:
        admin_mail = models.AdminMail(
            _id=0,
            text=msg.parse_entities(as_html=True) if msg.caption else None,
            gif=filename,
            sender=msg.from_user.id
        )
        await admin_mails_db.add(admin_mail)
    await open_admin_mail_menu(msg.from_user.id, admin_mail.id, state_data["msg_id"])
    await state.set_state(None)
    await msg.delete()


@dp.callback_query_handler(admin_mail_action.filter(action="add_buttons"))
async def add_buttons(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    mail = await safe_get_admin_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not mail:
        return
    msg = await cb.message.answer(
        "Щоб додати кнопки-посилання надішліть список у форматі\n<b>text_1 - link_1 | text_2 - link_2\ntext_3 - link_3\n...</b>",
        reply_markup=gen_cancel(
            admin_mail_action.new(
                id=callback_data["id"],
                action="open_admin_mail_menu"
            )
        )
    )
    await safe_del_msg(cb.from_user.id, cb.message.message_id)
    await state.set_state(states.InputStateGroup.admin_mail_buttons)
    await state.set_data({"msg_id": msg.message_id, "mail_id": callback_data["id"]})


def button_input_filter(msg: Message) -> bool:
    try:
        models.deserialize_buttons(msg.text)
        return True
    except ValueError:
        return False


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.admin_mail_buttons)
async def mail_buttons_input(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    admin_mail = await admin_mails_db.get(state_data["mail_id"])
    await msg.delete()
    try:
        admin_mail.buttons = models.deserialize_buttons(msg.text)
    except ValueError:
        try:
            await safe_edit_message(
                "❗️Невірний формат. Cпробуйте ще раз\nЩоб додати кнопки-посилання надішліть список у форматі\n<i><b>text_1 - link_1 | text_2 - link_2\ntext_3 - link_3\n...</b></i>",
                msg.from_user.id,
                state_data["msg_id"],
                reply_markup=gen_cancel(
                    admin_mail_action.new(
                        id=admin_mail.id,
                        action="open_mail_menu"
                    )
                )
            )
        except MessageNotModified:
            pass
        return
    await admin_mails_db.update(admin_mail)
    await state.set_state(None)
    await open_admin_mail_menu(msg.from_user.id, admin_mail.id, state_data["msg_id"])


@dp.callback_query_handler(admin_mail_action.filter(action="delete_admin_mail"))
async def delete_mail(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    admin_mail = await safe_get_admin_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not admin_mail:
        return
    await admin_mails_db.delete(admin_mail.id)
    await menu_admin_mails(cb, state)


async def mail_schedule_menu(uid: int, mail_id: int, msg_id: int):
    admin_mail = await admin_mails_db.get(mail_id)
    await bot.send_message(
        uid,
        f"<i>📩Час надсилання: {admin_mail.send_dt.strftime(models.DT_FORMAT) if admin_mail.send_dt else 'немає'}</i>",
        reply_markup=kb.gen_schedule_menu(admin_mail)
    )
    await safe_del_msg(uid, msg_id)


@dp.callback_query_handler(admin_mail_action.filter(action="schedule"), state="*")
async def mail_schedule_menu_cb(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    admin_mail = await safe_get_admin_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not admin_mail:
        return
    await state.set_state(None)
    await mail_schedule_menu(cb.from_user.id, int(callback_data["id"]), cb.message.message_id)


@dp.callback_query_handler(admin_mail_action.filter(action="schedule"), state="*")
async def mail_schedule_menu_cb(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    admin_mail = await safe_get_admin_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not admin_mail:
        return
    await state.set_state(None)
    await mail_schedule_menu(cb.from_user.id, int(callback_data["id"]), cb.message.message_id)


@dp.callback_query_handler(admin_mail_action.filter(action="edit_send_dt"))
async def edit_send_dt(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    admin_mail = await safe_get_admin_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not admin_mail:
        return
    msg = await cb.message.answer(
        "Введіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
        reply_markup=gen_cancel(admin_mail_action.new(callback_data["id"], "schedule"))
    )
    await state.set_state(states.InputStateGroup.admin_mail_send_dt)
    await state.set_data({"mail_id": int(callback_data["id"]), "msg_id": msg.message_id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.admin_mail_send_dt)
async def edit_send_dt(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    admin_mail = await safe_get_admin_mail(msg.from_user.id, state_data["mail_id"])
    if not admin_mail:
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
            reply_markup=gen_cancel(admin_mail_action.new(admin_mail.id, "schedule"))
        )
        return
    if tz.localize(input_dt) < datetime.now(tz=tz):
        await safe_edit_message(
            "❗️Введена дата не може бути у минулому. Спробуйте ще раз\n\n\
Введіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
            msg.from_user.id,
            state_data["msg_id"],
            reply_markup=gen_cancel(admin_mail_action.new(admin_mail.id, "schedule"))
        )
        return
    admin_mail.send_dt = input_dt
    await state.set_state(None)
    await admin_mails_db.update(admin_mail)
    await mail_schedule_menu(msg.from_user.id, admin_mail.id, state_data["msg_id"])


@dp.callback_query_handler(admin_mail_action.filter(action="del_send_dt"))
async def del_send_dt(cb: CallbackQuery, callback_data: dict):
    admin_mail = await safe_get_admin_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not admin_mail:
        return
    admin_mail.send_dt = None
    await admin_mails_db.update(admin_mail)
    await mail_schedule_menu(cb.from_user.id, admin_mail.id, cb.message.message_id)


@dp.callback_query_handler(admin_mail_action.filter(action="sendout"))
async def sendout(cb: CallbackQuery, callback_data: dict):
    admin_mail = await safe_get_admin_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not admin_mail:
        return
    await cb.message.answer(
        "Ви впевнені, що хочете запустити розсилку?",
        reply_markup=gen_confirmation(
            admin_mail_action.new(
                id=admin_mail.id,
                action="confirm_sendout"
            ),
            admin_mail_action.new(
                id=admin_mail.id,
                action="open_admin_mail_menu"
            )
        )
    )
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.callback_query_handler(admin_mail_action.filter(action="confirm_sendout"))
async def confirm_sendout(cb: CallbackQuery, callback_data: dict):
    # admin_mail = await safe_get_admin_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    admin_mail = await admin_mails_db.get(int(callback_data["id"]))
    bots_without_premium = []
    ubots_all = await bots_db.get_all()
    for ubot in ubots_all:
        if ubot.status == 1 and ubot.admin and ubot.premium == 0:
            bots_without_premium.append(ubot)
    for ubot in bots_without_premium:
        users = await user_db.get_by(bot=ubot.id)
        for user in users:
            new_mail_msgs = models.MailsQueue(
                _id=0,
                bot=ubot.id,
                user=user.id,
                mail_id=admin_mail.id,
                admin_status=True
            )
            await mails_queue_db.add(new_mail_msgs)
    admin_mail.active = 1
    await admin_mails_db.update(admin_mail)
    await safe_del_msg(cb.from_user.id, cb.message.message_id)
