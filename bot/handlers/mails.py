from bot.misc import *
from bot.keyboards import mails as kb
from bot.keyboards import bot_action, mail_action, gen_cancel, gen_ok, gen_confirmation
from datetime import datetime
from aiogram.utils.exceptions import ChatNotFound, BotBlocked


async def safe_get_mail(uid: int, mail_id: int, cb_id: int | None = None) -> models.Mail | None:
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
        mail = await mails_db.get(mail_id)
    except data_exc.RecordIsMissing:
        await alert()
        return None
    if mail.active == 1:
        await alert()
        return None
    return mail


@dp.callback_query_handler(bot_action.filter(action="mails"), state="*")
async def open_mail_list(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.set_state(None)
    bot_dc = await bots_db.get(int(callback_data["id"]))
    mails = await mails_db.get_by(bot=int(callback_data["id"]), active=0, status=0)
    await cb.message.answer(
        "<i>💡В цьому меню, можна створити, редагувати та запускати розсилки користувачам, які є у базі цього бота. \
</i>\n\n\
<b>📩Розсилки:</b>",
        reply_markup=kb.gen_mail_list(bot_dc, mails)
    )
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.callback_query_handler(bot_action.filter(action="add_mail"))
async def add_mail(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    bot_dc = await bots_db.get(int(callback_data["id"]))
    msg = await cb.message.answer(
        f"Надішліть текст, гіф, фото або відео з підписом. Переконайтеся, що чат з @{bot_dc.username} ініціалізовано. \nДинамічні змінні:\n\
<b>[any]\n[username]\n[first_name]\n[last_name]</b>",
        reply_markup=gen_cancel(
            bot_action.new(
                id=bot_dc.id,
                action="mails"
            )
        )
    )
    await state.set_state(states.InputStateGroup.mail)
    await state.set_data({"msg_id": msg.message_id, "bot_id": bot_dc.id, "edit": None})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.callback_query_handler(mail_action.filter(action="edit_mail"))
async def edit_mail(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    mail = await safe_get_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not mail:
        return
    msg = await cb.message.answer(
        "Надішліть текст, гіф, фото або відео з підписом.\nДинамічні змінні:\n\
<b>[any]\n[username]\n[first_name]\n[last_name]</b>",
        reply_markup=gen_cancel(
            callback_data=mail_action.new(
                id=mail.id,
                action="open_mail_menu"
            )
        )
    )
    await state.set_state(states.InputStateGroup.mail)
    await state.set_data({"msg_id": msg.message_id, "bot_id": mail.bot, "edit": mail.id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


async def open_mail_menu(uid: int, mail_id: int, msg_id: int):
    mail = await mails_db.get(mail_id)
    sched_text = "\n"
    if mail.send_dt:
        sched_text += f"\n<i>🕑Заплановано на: {mail.send_dt.strftime(models.DT_FORMAT)}</i>"
    if mail.del_dt:
        sched_text += f"\n<i>🗑Видалення: {mail.del_dt.strftime(models.DT_FORMAT)}</i>"
    mail_text_content = mail.text if mail.text else ""
    mail_text_content += sched_text
    bot_dc = await bots_db.get(mail.bot)
    if mail.photo:
        file = file_manager.get_file(mail.photo)
        await bot.send_photo(
            uid,
            file,
            caption=mail_text_content,
            reply_markup=kb.gen_mail_menu(bot_dc, mail)
        )
    elif mail.video:
        file = file_manager.get_file(mail.video)
        await bot.send_video(
            uid,
            file,
            caption=mail_text_content,
            reply_markup=kb.gen_mail_menu(bot_dc, mail)
        )
    elif mail.gif:
        file = file_manager.get_file(mail.gif)
        await bot.send_animation(
            uid,
            file,
            caption=mail_text_content,
            reply_markup=kb.gen_mail_menu(bot_dc, mail)
        )
    elif mail.text:
        await bot.send_message(
            uid,
            mail_text_content,
            reply_markup=kb.gen_mail_menu(bot_dc, mail)
        )
    await safe_del_msg(uid, msg_id)


@dp.callback_query_handler(mail_action.filter(action="open_mail_menu"), state="*")
async def open_mail_menu_cb(cb: CallbackQuery, callback_data: dict):
    mail = await safe_get_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not mail:
        return
    await open_mail_menu(cb.from_user.id, int(callback_data["id"]), cb.message.message_id)


async def initiate_ubot_file(mail: models.Mail) -> str:
    bot_dc = await bots_db.get(mail.bot)
    ubot = manager.bot_dict[bot_dc.token][0]
    users = await user_db.get_by(bot=bot_dc.id, status=1)
    if users == []:
        raise ChatNotFound("no users")
    user = users[0]
    try:
        if mail.photo:
            file = file_manager.get_file(mail.photo)
            ubot_msg = await ubot.send_photo(user.id, file)
            file_id = ubot_msg.photo[-1].file_id
        elif mail.video:
            file = file_manager.get_file(mail.video)
            ubot_msg = await ubot.send_video(user.id, file)
            file_id = ubot_msg.video.file_id
        elif mail.gif:
            file = file_manager.get_file(mail.gif)
            ubot_msg = await ubot.send_animation(user.id, file)
            file_id = ubot_msg.animation.file_id
        else:
            raise ValueError()
        await ubot.delete_message(
            user.id,
            ubot_msg.message_id
        )
    except BotBlocked:
        user.status = 0
        await user_db.update(user)
        file_id = await initiate_ubot_file(mail)
    return file_id

async def mail_input(
        msg: Message, state: FSMContext, text: str = None, photo: str = None, video: str = None, gif: str = None
):
    state_data = await state.get_data()
    bot_dc = await bots_db.get(state_data["bot_id"])
    if state_data["edit"]:
        mail = await mails_db.get(state_data["edit"])
    else:
        mail = models.Mail(
            _id=0,
            sender=msg.from_user.id,
            bot=state_data["bot_id"]
        )
    mail.text = text
    mail.photo = photo
    mail.video = video
    mail.gif = gif
    if mail.photo or mail.video or mail.gif:
        try:
            file_id = await initiate_ubot_file(mail)
        except ChatNotFound:
            await safe_edit_message(
                f"❗️Помилка. Ініціюйте чат з @{bot_dc.username}\n\n\
        Надішліть текст, гіф, фото або відео з підписом.\nДинамічні змінні:\n\
        <b>[any]\n[username]\n[first_name]\n[last_name]</b>",
                msg.from_user.id,
                state_data["msg_id"],
                reply_markup=gen_cancel(
                    bot_action.new(
                        id=bot_dc.id,
                        action="mails"
                    )
                )
            )
            await msg.delete()
            return
        mail.file_id = file_id
    if state_data["edit"]:
        await mails_db.update(mail)
    else:
        await mails_db.add(mail)
    await open_mail_menu(msg.from_user.id, mail.id, state_data["msg_id"])
    await state.set_state(None)
    await msg.delete()


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.mail)
async def mail_input_text(msg: Message, state: FSMContext):
    await mail_input(
        msg,
        state,
        text=msg.parse_entities(as_html=True) if msg.text else None
    )


@dp.message_handler(content_types=ContentTypes.PHOTO, state=states.InputStateGroup.mail)
async def mail_input_photo(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    filename = await file_manager.download_file(bot, state_data["bot_id"], msg.photo[-1].file_id)
    await mail_input(
        msg,
        state,
        text=msg.parse_entities(as_html=True) if msg.caption else None,
        photo=filename
    )


@dp.message_handler(content_types=ContentTypes.VIDEO, state=states.InputStateGroup.mail)
async def mail_input_video(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    filename = await file_manager.download_file(bot, state_data["bot_id"], msg.video.file_id)
    await mail_input(
        msg,
        state,
        text=msg.parse_entities(as_html=True) if msg.caption else None,
        video=filename
    )


@dp.message_handler(content_types=ContentTypes.ANIMATION, state=states.InputStateGroup.mail)
async def mail_input_gif(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    filename = await file_manager.download_file(bot, state_data["bot_id"], msg.animation.file_id)
    await mail_input(
        msg,
        state,
        text=msg.parse_entities(as_html=True) if msg.caption else None,
        gif=filename
    )


@dp.callback_query_handler(mail_action.filter(action="add_buttons"))
async def add_buttons(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    mail = await safe_get_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not mail:
        return
    msg = await cb.message.answer(
        "Щоб додати кнопки-посилання надішліть список у форматі\n\
<b>text_1 - link_1 | text_2 - link_2\ntext_3 - link_3\n...</b>",
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
    mail = await mails_db.get(state_data["mail_id"])
    await msg.delete()
    try:
        input_buttons = models.deserialize_buttons(msg.text)
        if not models.is_valid_link(input_buttons):
            await safe_edit_message(
            "❗️Невірне посилання в одній з кнопок. Cпробуйте ще раз\nЩоб додати кнопки-посилання надішліть список у форматі\n\
<i><b>text_1 - link_1 | text_2 - link_2\ntext_3 - link_3\n...</b></i>",
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
    except ValueError:
        await safe_edit_message(
            "❗️Невірний формат. Cпробуйте ще раз\nЩоб додати кнопки-посилання надішліть список у форматі\n\
<i><b>text_1 - link_1 | text_2 - link_2\ntext_3 - link_3\n...</b></i>",
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
    mail.buttons = input_buttons
    await mails_db.update(mail)
    await state.set_state(None)
    await open_mail_menu(msg.from_user.id, mail.id, state_data["msg_id"])


@dp.callback_query_handler(mail_action.filter(action="delete_mail"))
async def delete_mail(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    mail = await safe_get_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not mail:
        return
    await mails_db.delete(mail.id)
    await open_mail_list(cb, {"id": mail.bot}, state)


async def mail_schedule_menu(uid: int, mail_id: int, msg_id: int):
    mail = await mails_db.get(mail_id)
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
    if not mail:
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
            reply_markup=gen_cancel(mail_action.new(mail.id, "schedule"))
        )
        return
    if tz.localize(input_dt) < datetime.now(tz=tz):
        await safe_edit_message(
            "❗️Введена дата не може бути у минулому. Спробуйте ще раз\n\n\
Введіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
            msg.from_user.id,
            state_data["msg_id"],
            reply_markup=gen_cancel(mail_action.new(mail.id, "schedule"))
        )
        return
    if mail.del_dt and (mail.del_dt - input_dt).total_seconds() / 3600 > 47.75:
        await safe_edit_message(
            "❗️Різниця між часом надсилання та часом автовидалення не може перевищувати 48 годин. Спробуйте ще раз\n\n\
Введіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
            msg.from_user.id,
            state_data["msg_id"],
            reply_markup=gen_cancel(mail_action.new(mail.id, "schedule"))
        )
        return
    mail.send_dt = input_dt
    await state.set_state(None)
    await mails_db.update(mail)
    await mail_schedule_menu(msg.from_user.id, mail.id, state_data["msg_id"])


@dp.callback_query_handler(mail_action.filter(action="del_send_dt"))
async def del_send_dt(cb: CallbackQuery, callback_data: dict):
    mail = await safe_get_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not mail:
        return
    mail.send_dt = None
    await mails_db.update(mail)
    await mail_schedule_menu(cb.from_user.id, mail.id, cb.message.message_id)


@dp.callback_query_handler(mail_action.filter(action="edit_del_dt"))
async def edit_del_dt(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    mail = await safe_get_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not mail:
        return
    bot_dc = await bots_db.get(mail.bot)
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
    await safe_del_msg(msg.from_user.id, msg.message_id)
    state_data = await state.get_data()
    mail = await safe_get_mail(msg.from_user.id, state_data["mail_id"])
    if not mail:
        return
    try:
        input_dt = datetime.strptime(msg.text, models.DT_FORMAT)
    except ValueError:
        await safe_edit_message(
            "❗️Невірний формат. Спробуйте ще раз\n\nВведіть дату та час у форматі <i>[H:M d.m.Y]</i>\n\
Приклад: <i>16:20 12.05.2023</i>",
            msg.from_user.id,
            state_data["msg_id"],
            reply_markup=gen_cancel(mail_action.new(mail.id, "schedule"))
        )
        return
    if tz.localize(input_dt) < datetime.now(tz=tz):
        await safe_edit_message(
            "❗️Введена дата не може бути у минулому. Спробуйте ще раз\n\n\
Введіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
            msg.from_user.id,
            state_data["msg_id"],
            reply_markup=gen_cancel(mail_action.new(mail.id, "schedule"))
        )
        return
    if mail.send_dt and (input_dt - mail.send_dt).total_seconds() / 3600 > 47.75:
        await safe_edit_message(
            "❗️Різниця між часом надсилання та часом автовидалення не може перевищувати 48 годин. Спробуйте ще раз\n\n\
Введіть дату та час у форматі <i>[H:M d.m.Y]</i>\nПриклад: <i>16:20 12.05.2023</i>",
            msg.from_user.id,
            state_data["msg_id"],
            reply_markup=gen_cancel(mail_action.new(mail.id, "schedule"))
        )
        return
    mail.del_dt = input_dt
    await mails_db.update(mail)
    await state.set_state(None)
    await mail_schedule_menu(msg.from_user.id, mail.id, state_data["msg_id"])


@dp.callback_query_handler(mail_action.filter(action="del_del_dt"))
async def del_del_dt(cb: CallbackQuery, callback_data: dict):
    mail = await safe_get_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not mail:
        return
    bot_dc = await bots_db.get(mail.bot)
    if bot_dc.premium <= 0:
        await cb.answer("⭐️Лише для преміум ботів")
        return
    mail.del_dt = None
    await mails_db.update(mail)
    await mail_schedule_menu(cb.from_user.id, mail.id, cb.message.message_id)


@dp.callback_query_handler(mail_action.filter(action="sendout"))
async def sendout(cb: CallbackQuery, callback_data: dict):
    mail = await safe_get_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not mail:
        return
    if mail.del_dt and (tz.localize(mail.del_dt) - datetime.now(tz=tz)).total_seconds() / 3600 > 47.75:
        await cb.answer(
            "❗️Різниця між часом надсилання та часом автовидалення не може перевищувати 48 годин.\n\
Змініть час автовидалення автовидалення",
            show_alert=True
        )
        return
    await cb.message.answer(
        "Ви впевнені, що хочете запустити розсилку?",
        reply_markup=gen_confirmation(
            mail_action.new(
                id=mail.id,
                action="confirm_sendout"
            ),
            mail_action.new(
                id=mail.id,
                action="open_mail_menu"
            )
        )
    )
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.callback_query_handler(mail_action.filter(action="confirm_sendout"))
async def confirm_sendout(cb: CallbackQuery, callback_data: dict):
    mail = await safe_get_mail(cb.from_user.id, int(callback_data["id"]), cb.id)
    if not mail:
        return
    create_task(gig.enqueue_mail(mail))
    bot_dc = await bots_db.get(mail.bot)
    await cb.message.answer(
        f"Розсилка {gen_hex_caption(mail.id)} в боті @{bot_dc.username} була поставлена в чергу. Вам прийде повідомлення коли вона розпочнеться",
        reply_markup=gen_ok(
            bot_action.new(
                id=mail.bot,
                action="mails"
            )
        )
    )
    await safe_del_msg(cb.from_user.id, cb.message.message_id)
