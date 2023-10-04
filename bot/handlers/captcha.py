import bot.handlers.settings
from bot.misc import *
from bot.keyboards import captcha as kb
from bot.keyboards import bot_action, captcha_action, gen_cancel


async def open_captcha_menu(uid: int, captcha_id: int, msg_id: int):
    captcha = await captchas_db.get(captcha_id)
    bot_dc = await bots_db.get(captcha.bot)
    if captcha.photo:
        file = file_manager.get_file(captcha.photo)
        await bot.send_photo(uid, file, caption=captcha.text, reply_markup=kb.gen_captcha_menu(bot_dc, captcha))
    elif captcha.video:
        file = file_manager.get_file(captcha.video)
        await bot.send_video(uid, file, caption=captcha.text, reply_markup=kb.gen_captcha_menu(bot_dc, captcha))
    elif captcha.gif:
        file = file_manager.get_file(captcha.gif)
        await bot.send_animation(uid, file, caption=captcha.text, reply_markup=kb.gen_captcha_menu(bot_dc, captcha))
    else:
        await bot.send_message(uid, captcha.text, reply_markup=kb.gen_captcha_menu(bot_dc, captcha))
    await safe_del_msg(uid, msg_id)


@dp.callback_query_handler(bot_action.filter(action="captcha"), state="*")
async def open_captcha_menu_cb(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.set_state(None)
    captcha = (await captchas_db.get_by(bot=int(callback_data["id"])))[0]
    await open_captcha_menu(cb.from_user.id, captcha.id, cb.message.message_id)


@dp.callback_query_handler(captcha_action.filter(action="captcha_on"))
async def captcha_on(cb: CallbackQuery, callback_data: dict):
    captcha = await captchas_db.get(int(callback_data["id"]))
    captcha.active = True
    await captchas_db.update(captcha)
    await open_captcha_menu(cb.from_user.id, captcha.id, cb.message.message_id)


@dp.callback_query_handler(captcha_action.filter(action="captcha_off"))
async def captcha_off(cb: CallbackQuery, callback_data: dict):
    captcha = await captchas_db.get(int(callback_data["id"]))
    bot_dc = await bots_db.get(captcha.bot)
    if bot_dc.premium <= 0:
        await cb.answer(
            "❗️Вимкнення капчі доступно лише для преміум-ботів",
            show_alert=True
        )
        return
    captcha.active = False
    await captchas_db.update(captcha)
    await open_captcha_menu(cb.from_user.id, captcha.id, cb.message.message_id)


@dp.callback_query_handler(captcha_action.filter(action="set_captcha"))
async def set_captcha(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    captcha = await captchas_db.get(int(callback_data["id"]))
    msg = await cb.message.answer(
        "Надішліть текст, гіф, фото або відео з підписом.\nДинамічні змінні:\n<b>[any]\n[username]\n[first_name]\n[last_name]</b>",
        reply_markup=gen_cancel(bot_action.new(id=captcha.bot, action="captcha"))
    )
    await state.set_state(states.InputStateGroup.captcha)
    await state.set_data({"captcha_id": int(callback_data["id"]), "msg_id": msg.message_id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.captcha)
async def set_captcha_text(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    await state.set_state(None)
    captcha = await captchas_db.get(state_data["captcha_id"])
    captcha.text = msg.parse_entities(as_html=True) if msg.text else None
    captcha.photo = None
    captcha.video = None
    captcha.gif = None
    await captchas_db.update(captcha)
    await msg.delete()
    await open_captcha_menu(msg.from_user.id, captcha.id, state_data["msg_id"])


@dp.message_handler(content_types=ContentTypes.PHOTO, state=states.InputStateGroup.captcha)
async def set_captcha_photo(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    await state.set_state(None)
    captcha = await captchas_db.get(state_data["captcha_id"])
    captcha.text = msg.parse_entities(as_html=True) if msg.caption else None
    captcha.photo = await file_manager.download_file(bot, captcha.bot, msg.photo[-1].file_id)
    captcha.video = None
    captcha.gif = None
    await captchas_db.update(captcha)
    await msg.delete()
    await open_captcha_menu(msg.from_user.id, captcha.id, state_data["msg_id"])


@dp.message_handler(content_types=ContentTypes.VIDEO, state=states.InputStateGroup.captcha)
async def set_captcha_video(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    await state.set_state(None)
    captcha = await captchas_db.get(state_data["captcha_id"])
    captcha.text = msg.parse_entities(as_html=True) if msg.caption else None
    captcha.photo = None
    captcha.video = await file_manager.download_file(bot, captcha.bot, msg.video.file_id)
    captcha.gif = None
    await captchas_db.update(captcha)
    await msg.delete()
    await open_captcha_menu(msg.from_user.id, captcha.id, state_data["msg_id"])


@dp.message_handler(content_types=ContentTypes.ANIMATION, state=states.InputStateGroup.captcha)
async def set_captcha_gif(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    await state.set_state(None)
    captcha = await captchas_db.get(state_data["captcha_id"])
    captcha.text = msg.parse_entities(as_html=True) if msg.caption else None
    captcha.photo = None
    captcha.video = None
    captcha.gif = await file_manager.download_file(bot, captcha.bot, msg.animation.file_id)
    await captchas_db.update(captcha)
    await msg.delete()
    await open_captcha_menu(msg.from_user.id, captcha.id, state_data["msg_id"])


@dp.callback_query_handler(captcha_action.filter(action="set_buttons"))
async def set_buttons_entry(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    captcha = await captchas_db.get(int(callback_data["id"]))
    msg = await cb.message.answer(
        "Щоб додати кнопки-посилання надішліть список у форматі\n<b>text_1 | text_2 \ntext_3\n...</b>",
        reply_markup=gen_cancel(bot_action.new(id=captcha.bot, action="captcha"))
    )
    await state.set_state(states.InputStateGroup.captcha_buttons)
    await state.set_data({"msg_id": msg.message_id, "captcha_id": captcha.id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.captcha_buttons)
async def set_buttons(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    await msg.delete()
    await state.set_state(None)
    captcha = await captchas_db.get(state_data["captcha_id"])
    try:
        captcha.buttons = models.deserialize_reply_buttons(msg.text)
    except ValueError:
        try:
            await bot.edit_message_text(
                "❗️Невірний формат. Cпробуйте ще раз\nЩоб додати кнопки-посилання надішліть список у форматі\n<b>text_1 | text_2 \ntext_3\n...</b>",
                msg.from_user.id,
                state_data["msg_id"],
                reply_markup=gen_cancel(
                    bot_action.new(
                        id=captcha.bot,
                        action="captcha"
                    )
                )
            )
        except MessageNotModified:
            pass
        return
    await captchas_db.update(captcha)
    await open_captcha_menu(msg.from_user.id, captcha.id, state_data["msg_id"])


@dp.callback_query_handler(lambda cb: cb.data == "reply_buttons_info")
async def reply_button_info(cb: CallbackQuery):
    await cb.answer("Користувачі будуть бачити ці кнопки як реплай-клавіатуру (кнопки знизу над клавіатурою)")


async def captcha_schedule_menu(uid: int, captcha_id: int, msg_id: int):
    captcha = await captchas_db.get(captcha_id)
    await bot.send_message(
        uid,
        f"<i>♻️Затримка автовидалення: {f'{captcha.del_delay // 60} хв. {captcha.del_delay % 60} сек.' if captcha.del_delay else 'немає'}</i>",
        reply_markup=kb.gen_timings_menu(captcha)
    )
    await safe_del_msg(uid, msg_id)


@dp.callback_query_handler(captcha_action.filter(action="schedule"), state="*")
async def schedule_captcha(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.set_state(None)
    await captcha_schedule_menu(cb.from_user.id, int(callback_data["id"]), cb.message.message_id)


@dp.callback_query_handler(captcha_action.filter(action="edit_del_delay"))
async def edit_del_delay(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    captcha = await captchas_db.get(int(callback_data["id"]))
    msg = await cb.message.answer(
        'Введіть затримку надсилання у форматі "mm:ss", наприклад 05:30.\nЧас затримки не може перевищувати 1 години.',
        reply_markup=gen_cancel(
            callback_data=captcha_action.new(
                id=captcha.id,
                action="schedule"
            )
        )
    )
    await state.set_state(states.InputStateGroup.captcha_del_delay)
    await state.set_data({"captcha_id": captcha.id, "msg_id": msg.message_id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.captcha_del_delay)
async def edit_del_delay(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    captcha = await captchas_db.get(state_data["captcha_id"])
    if re.match(r'^\d{2}:\d{2}$', msg.text) and 0 < convert_to_seconds(msg.text) < 3600:
        await state.set_state(None)
        captcha.del_delay = int(convert_to_seconds(msg.text))
        await captchas_db.update(captcha)
        await msg.delete()
        await captcha_schedule_menu(msg.from_user.id, captcha.id, state_data["msg_id"])
    else:
        await safe_del_msg(msg.from_user.id, msg.message_id)
        try:
            await bot.edit_message_text(
                '❗️Невірний формат. Спробуйте ще раз\nВведіть затримку надсилання у форматі "mm:ss", наприклад 05:30.\nЧас затримки не може перевищувати 1 години.',
                msg.from_user.id,
                state_data["msg_id"],
                reply_markup=gen_cancel(
                    callback_data=captcha_action.new(
                        id=captcha.id,
                        action="schedule"
                    )
                )
            )
        except MessageNotModified:
            pass


@dp.callback_query_handler(captcha_action.filter(action="del_del_delay"))
async def del_del_delay(cb: CallbackQuery, callback_data: dict):
    captcha = await captchas_db.get(int(callback_data["id"]))
    captcha.del_delay = None
    await captchas_db.update(captcha)
    await captcha_schedule_menu(cb.from_user.id, captcha.id, cb.message.message_id)


def convert_to_seconds(time_str):
    minutes, seconds = map(int, time_str.split(':'))
    total_seconds = minutes * 60 + seconds
    return total_seconds

