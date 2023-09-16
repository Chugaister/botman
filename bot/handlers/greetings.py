from bot.misc import *
from bot.keyboards import greetings as kb
from bot.keyboards import bot_action, greeting_action, gen_cancel


@dp.callback_query_handler(bot_action.filter(action="greetings"), state="*")
async def greeting_list(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.set_state(None)
    bot_dc = await bots_db.get(int(callback_data["id"]))
    greetings = await greeting_db.get_by(bot=int(callback_data["id"]))
    await cb.message.answer(
        "<i>💡Привітання- це повідомлення, які приходитимуть користувачу після проходження каптчі, \
якщо вона активна, інакше- після подачі заявки на вступ до каналу. \
У вас є можливість створювати довільну кількість привітань, налаштовувати час надсилання та видалення, \
прикріпляти кнопки-посилання. Не забудьте увімкнути привітання після його створення.</i>\n\n\
<b>👋Список привітань</b>:",
        reply_markup=kb.gen_greeting_list(bot_dc, greetings)
    )
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


async def send_greeting_menu(uid: int, greeting_id: int, msg_id: int):
    greeting = await greeting_db.get(greeting_id)
    bot_dc = await bots_db.get(greeting.bot)
    if greeting.photo:
        file = file_manager.get_file(greeting.photo)
        await bot.send_photo(
            uid,
            file,
            caption=greeting.text,
            reply_markup=kb.gen_greeting_menu(bot_dc, greeting)
        )
    elif greeting.video:
        file = file_manager.get_file(greeting.video)
        await bot.send_video(
            uid,
            file,
            caption=greeting.text,
            reply_markup=kb.gen_greeting_menu(bot_dc, greeting)
        )
    elif greeting.gif:
        file = file_manager.get_file(greeting.gif)
        await bot.send_animation(
            uid,
            file,
            caption=greeting.text,
            reply_markup=kb.gen_greeting_menu(bot_dc, greeting)
        )
    elif greeting.text:
        await bot.send_message(
            uid,
            greeting.text,
            reply_markup=kb.gen_greeting_menu(bot_dc, greeting)
        )
    await safe_del_msg(uid, msg_id)


@dp.callback_query_handler(greeting_action.filter(action="open_greeting_menu"), state="*")
async def send_greeting_menu_cb(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.set_state(None)
    await send_greeting_menu(cb.from_user.id, int(callback_data["id"]), cb.message.message_id)


@dp.callback_query_handler(bot_action.filter(action="add_greeting"))
async def add_greeting(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    bot_dc = await bots_db.get(int(callback_data["id"]))
    msg = await cb.message.answer(
        "Надішліть текст, гіф, фото або відео з підписом.\n\
Динамічні змінні:\n<b>[any]\n[username]\n[first_name]\n[last_name]</b>",
        reply_markup=gen_cancel(
            bot_action.new(
                id=bot_dc.id,
                action="greetings"
            )
        )
    )
    await state.set_state(states.InputStateGroup.greeting)
    await state.set_data({"msg_id": msg.message_id, "bot_id": bot_dc.id, "edit": None})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.callback_query_handler(greeting_action.filter(action="edit_greeting"))
async def edit_gereting(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    greeting = await greeting_db.get(int(callback_data["id"]))
    msg = await cb.message.answer(
        "Надішліть текст, гіф, фото або відео з підписом.\n\
Динамічні змінні:\n<b>[any]\n[username]\n[first_name]\n[last_name]</b>",
        reply_markup=gen_cancel(
            greeting_action.new(
                id=greeting.id,
                action="open_greeting_menu"
            )
        )
    )
    await state.set_state(states.InputStateGroup.greeting)
    await state.set_data({"msg_id": msg.message_id, "bot_id": greeting.bot, "edit": greeting.id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.greeting)
async def greeting_input_text(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    if state_data["edit"]:
        greeting = await greeting_db.get(state_data["edit"])
        greeting.text = msg.parse_entities(as_html=True) if msg.text else None
        greeting.photo = None
        greeting.video = None
        greeting.gif = None
        await greeting_db.update(greeting)
    else:
        greeting = models.Greeting(
            _id=0,
            bot=state_data["bot_id"],
            text=msg.parse_entities(as_html=True) if msg.text else None,
            photo=None,
            video=None,
            gif=None
        )
        await greeting_db.add(greeting)
    await send_greeting_menu(msg.from_user.id, greeting.id, state_data["msg_id"])
    await state.set_state(None)
    await msg.delete()


@dp.message_handler(content_types=ContentTypes.PHOTO, state=states.InputStateGroup.greeting)
async def greeting_input_photo(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    filename = await file_manager.download_file(bot, state_data["bot_id"], msg.photo[-1].file_id)
    if state_data["edit"]:
        greeting = await greeting_db.get(state_data["edit"])
        greeting.text = msg.parse_entities(as_html=True) if msg.caption else None
        greeting.photo = filename
        greeting.video = None
        greeting.gif = None
        await greeting_db.update(greeting)
    else:
        greeting = models.Greeting(
            _id=0,
            bot=state_data["bot_id"],
            text=msg.parse_entities(as_html=True) if msg.caption else None,
            photo=filename,
            video=None,
            gif=None
        )
        await greeting_db.add(greeting)
    await send_greeting_menu(msg.from_user.id, greeting.id, state_data["msg_id"])
    await state.set_state(None)
    await msg.delete()


@dp.message_handler(content_types=ContentTypes.VIDEO, state=states.InputStateGroup.greeting)
async def greeting_input_video(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    filename = await file_manager.download_file(bot, state_data["bot_id"], msg.video.file_id)
    if state_data["edit"]:
        greeting = await greeting_db.get(state_data["edit"])
        greeting.text = msg.parse_entities(as_html=True) if msg.caption else None
        greeting.photo = None
        greeting.video = filename
        greeting.gif = None
        await greeting_db.update(greeting)
    else:
        greeting = models.Greeting(
            _id=0,
            bot=state_data["bot_id"],
            text=msg.parse_entities(as_html=True) if msg.caption else None,
            photo=None,
            video=filename,
            gif=None
        )
        await greeting_db.add(greeting)
    await send_greeting_menu(msg.from_user.id, greeting.id, state_data["msg_id"])
    await state.set_state(None)
    await msg.delete()


@dp.message_handler(content_types=ContentTypes.ANIMATION, state=states.InputStateGroup.greeting)
async def greeting_input_gif(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    filename = await file_manager.download_file(bot, state_data["bot_id"], msg.animation.file_id)
    if state_data["edit"]:
        greeting = await greeting_db.get(state_data["edit"])
        greeting.text = msg.parse_entities(as_html=True) if msg.caption else None
        greeting.photo = None
        greeting.video = None
        greeting.gif = filename
        await greeting_db.update(greeting)
    else:
        greeting = models.Greeting(
            _id=0,
            bot=state_data["bot_id"],
            text=msg.parse_entities(as_html=True) if msg.caption else None,
            photo=None,
            video=None,
            gif=await file_manager.download_file(bot, state_data["bot_id"], msg.animation.file_id)
        )
        await greeting_db.add(greeting)
    await send_greeting_menu(msg.from_user.id, greeting.id, state_data["msg_id"])
    await state.set_state(None)
    await msg.delete()


@dp.callback_query_handler(greeting_action.filter(action="delete_greeting"))
async def delete_greeting(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    greeting = await greeting_db.get(int(callback_data["id"]))
    callback_data["id"] = greeting.bot
    await greeting_db.delete(greeting.id)
    await greeting_list(cb, callback_data, state)


@dp.callback_query_handler(greeting_action.filter(action="greeting_off"))
async def greeting_off(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    greeting = await greeting_db.get(int(callback_data["id"]))
    greeting.active = False
    await greeting_db.update(greeting)
    await send_greeting_menu_cb(cb, callback_data, state)


@dp.callback_query_handler(greeting_action.filter(action="greeting_on"))
async def greeting_on(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    greeting = await greeting_db.get(int(callback_data["id"]))
    greeting.active = True
    await greeting_db.update(greeting)
    await send_greeting_menu_cb(cb, callback_data, state)


@dp.callback_query_handler(greeting_action.filter(action="add_greeting_buttons"))
async def add_greeting_buttons(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    msg = await cb.message.answer(
        "Щоб додати кнопки-посилання надішліть список у форматі\n<b>\
text_1 - link_1 | text_2 - link_2\ntext_3 - link_3\n...</b>",
        reply_markup=gen_cancel(
            greeting_action.new(
                id=callback_data["id"],
                action="open_greeting_menu"
            )
        )
    )
    await safe_del_msg(cb.from_user.id, cb.message.message_id)
    await state.set_state(states.InputStateGroup.greeting_buttons)
    await state.set_data({"msg_id": msg.message_id, "greeting_id": callback_data["id"]})


def button_input_filter(msg: Message) -> bool:
    try:
        models.deserialize_buttons(msg.text)
        return True
    except ValueError:
        return False


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.greeting_buttons)
async def greeting_buttons_input(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    await msg.delete()
    greeting = await greeting_db.get(state_data["greeting_id"])
    try:
        greeting.buttons = models.deserialize_buttons(msg.text)
    except ValueError:
        try:
            await bot.edit_message_text(
                "❗️Невірний формат. Cпробуйте ще раз\nЩоб додати кнопки-посилання надішліть список у форматі\n\
<b>text_1 - link_1 | text_2 - link_2\ntext_3 - link_3\n...</b>",
                msg.from_user.id,
                state_data["msg_id"],
                reply_markup=gen_cancel(
                    greeting_action.new(
                        id=greeting.id,
                        action="open_greeting_menu"
                    )
                )
            )
        except MessageNotModified:
            pass
        return
    await greeting_db.update(greeting)
    await state.set_state(None)
    await send_greeting_menu(msg.from_user.id, greeting.id, state_data["msg_id"])


async def greeting_schedule_menu(uid: int, greeting_id: int, msg_id: int):
    greeting = await greeting_db.get(greeting_id)
    await bot.send_message(
        uid,
        f"💡<i>В цьому меню ви можете налаштувати затримку надсилання та видалення привітання</i>\n\n\
📩Затримка надсилання: {f'{greeting.send_delay // 60} хв. {greeting.send_delay % 60} сек.' if greeting.send_delay else 'немає'}\n\
♻️Затримка автовидалення: {f'{greeting.del_delay // 60 } хв. {greeting.del_delay % 60} сек.' if greeting.del_delay else 'немає'}",
        reply_markup=kb.gen_timings_menu(greeting)
    )
    await safe_del_msg(uid, msg_id)


@dp.callback_query_handler(greeting_action.filter(action="schedule"), state="*")
async def greeting_schedule_menu_cb(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.set_state(None)
    await greeting_schedule_menu(cb.from_user.id, int(callback_data["id"]), cb.message.message_id)


@dp.callback_query_handler(greeting_action.filter(action="edit_send_delay"))
async def edit_send_delay(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    msg = await cb.message.answer(
        'Введіть затримку надсилання у форматі "mm:ss", наприклад 05:30.\n\
Час затримки не може перевищувати 1 години.',
        reply_markup=gen_cancel(
            callback_data=greeting_action.new(
                callback_data["id"],
                "schedule"  
            )
        )
    )
    await state.set_state(states.InputStateGroup.greeting_send_delay)
    await state.set_data({"greeting_id": int(callback_data["id"]), "msg_id": msg.message_id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.message_handler(lambda msg: msg, content_types=ContentTypes.TEXT, state=states.InputStateGroup.greeting_send_delay)
async def edit_send_delay(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    if re.match(r'^\d{2}:\d{2}$', msg.text) and 0 < convert_to_seconds(msg.text) < 3600 :
        await state.set_state(None)       
        greeting = await greeting_db.get(state_data["greeting_id"])
        greeting.send_delay = int(convert_to_seconds(msg.text))
        await greeting_db.update(greeting)
        await msg.delete()
        await greeting_schedule_menu(msg.from_user.id, greeting.id, state_data["msg_id"])
    else:
        await safe_del_msg(msg.from_user.id, msg.message_id)
        try:
            await bot.edit_message_text(
                '❗️Невірний формат\nВведіть затримку надсилання у форматі "mm:ss", наприклад 05:30.\n\
Час затримки не може перевищувати 1 години.',
                msg.from_user.id,
                state_data["msg_id"],
                reply_markup=gen_cancel(
                    callback_data=greeting_action.new(
                        state_data["greeting_id"],
                        "schedule"
                    )
                )
            )
        except MessageNotModified:
            pass        


@dp.callback_query_handler(greeting_action.filter(action="del_send_delay"))
async def del_send_delay(cb: CallbackQuery, callback_data: dict):
    greeting = await greeting_db.get(int(callback_data["id"]))
    greeting.send_delay = None
    await greeting_db.update(greeting)
    await greeting_schedule_menu(cb.from_user.id, int(callback_data["id"]), cb.message.message_id)


@dp.callback_query_handler(greeting_action.filter(action="edit_del_delay"))
async def edit_del_delay(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    greeting = await greeting_db.get(int(callback_data["id"]))
    bot_dc = await bots_db.get(greeting.bot)
    msg = await cb.message.answer(
        'Введіть затримку надсилання у форматі "mm:ss", наприклад 05:30.\n\
Час затримки не може перевищувати 1 години.',
        reply_markup=gen_cancel(
            callback_data=greeting_action.new(
                callback_data["id"],
                "schedule"
            )
        )
    )
    await state.set_state(states.InputStateGroup.greeting_del_delay)
    await state.set_data({"greeting_id": int(callback_data["id"]), "msg_id": msg.message_id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.greeting_del_delay)
async def edit_del_delay(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    if re.match(r'^\d{2}:\d{2}$', msg.text) and 0 < convert_to_seconds(msg.text) < 3600 :
        await state.set_state(None)
        greeting = await greeting_db.get(state_data["greeting_id"])
        greeting.del_delay = int(convert_to_seconds(msg.text))
        await greeting_db.update(greeting)
        await msg.delete()
        await greeting_schedule_menu(msg.from_user.id, greeting.id, state_data["msg_id"])
    else:
        await safe_del_msg(msg.from_user.id, msg.message_id)
        try:
            await bot.edit_message_text(
                'Введіть затримку надсилання у форматі "mm:ss", наприклад 05:30.\n\
Час затримки не може перевищувати 1 години.',
                msg.from_user.id,
                state_data["msg_id"],
                reply_markup=gen_cancel(
                    callback_data=greeting_action.new(
                        state_data["greeting_id"],
                        "schedule"
                    )
                )
            )
        except MessageNotModified:
            pass


@dp.callback_query_handler(greeting_action.filter(action="del_del_delay"))
async def del_del_delay(cb: CallbackQuery, callback_data: dict):
    greeting = await greeting_db.get(int(callback_data["id"]))
    greeting.del_delay = None
    await greeting_db.update(greeting)
    await greeting_schedule_menu(cb.from_user.id, int(callback_data["id"]), cb.message.message_id)


def convert_to_seconds(time_str):
    minutes, seconds = map(int, time_str.split(':'))
    total_seconds = minutes * 60 + seconds
    return total_seconds
