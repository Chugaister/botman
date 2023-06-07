import bot.handlers.greetings
from bot.misc import *
from bot.keyboards import greetings as kb
from bot.keyboards import bot_action, greeting_action, gen_cancel


@dp.callback_query_handler(bot_action.filter(action="greetings"), state="*")
async def greeting_list(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.set_state(None)
    bot_dc = bots_db.get(int(callback_data["id"]))
    greetings = greeting_db.get_by(bot=int(callback_data["id"]))
    await cb.message.answer(
        "{text4}Привітання:",
        reply_markup=kb.gen_greeting_list(bot_dc, greetings)
    )
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


async def send_greeting_menu(uid: int, greeting_id: int, msg_id: int):
    greeting = greeting_db.get(greeting_id)
    bot_dc = bots_db.get(greeting.bot)
    if greeting.photo:
        file = await file_manager.get_file(greeting.photo)
        await bot.send_photo(
            uid,
            file,
            caption=greeting.text,
            reply_markup=kb.gen_greeting_menu(bot_dc, greeting)
        )
    elif greeting.video:
        file = await file_manager.get_file(greeting.video)
        await bot.send_video(
            uid,
            file,
            caption=greeting.text,
            reply_markup=kb.gen_greeting_menu(bot_dc, greeting)
        )
    elif greeting.gif:
        file = await file_manager.get_file(greeting.gif)
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
    bot_dc = bots_db.get(int(callback_data["id"]))
    msg = await cb.message.answer(
        "Надішліть текст, гіф, фото або відео з підписом",
        reply_markup=gen_cancel(
            bot_action.new(
                id=bot_dc.id,
                action="greetings"
            )
        )
    )
    await state.set_state(states.InputStateGroup.greeting)
    await state.set_data({"msg_id": msg.message_id, "bot_id": bot_dc.id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.greeting)
async def greeting_input_text(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    greeting = models.Greeting(
        _id=0,
        bot=state_data["bot_id"],
        text=msg.text,
        photo=None,
        video=None,
        gif=None
    )
    greeting_db.add(greeting)
    await send_greeting_menu(msg.from_user.id, greeting.id, state_data["msg_id"])
    await state.set_state(None)
    await msg.delete()


@dp.message_handler(content_types=ContentTypes.PHOTO, state=states.InputStateGroup.greeting)
async def greeting_input_photo(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    greeting = models.Greeting(
        _id=0,
        bot=state_data["bot_id"],
        text=msg.caption,
        photo=await file_manager.download_file(bot, state_data["bot_id"], msg.photo[-1].file_id),
        video=None,
        gif=None
    )
    greeting_db.add(greeting)
    await send_greeting_menu(msg.from_user.id, greeting.id, state_data["msg_id"])
    await state.set_state(None)
    await msg.delete()


@dp.message_handler(content_types=ContentTypes.VIDEO, state=states.InputStateGroup.greeting)
async def greeting_input_video(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    greeting = models.Greeting(
        _id=0,
        bot=state_data["bot_id"],
        text=msg.caption,
        photo=None,
        video=await file_manager.download_file(bot, state_data["bot_id"], msg.video.file_id),
        gif=None
    )
    greeting_db.add(greeting)
    await send_greeting_menu(msg.from_user.id, greeting.id, state_data["msg_id"])
    await state.set_state(None)
    await msg.delete()


@dp.message_handler(content_types=ContentTypes.ANIMATION, state=states.InputStateGroup.greeting)
async def greeting_input_gif(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    greeting = models.Greeting(
        _id=0,
        bot=state_data["bot_id"],
        text=msg.caption,
        photo=None,
        video=None,
        gif=await file_manager.download_file(bot, state_data["bot_id"], msg.animation.file_id)
    )
    greeting_db.add(greeting)
    await send_greeting_menu(msg.from_user.id, greeting.id, state_data["msg_id"])
    await state.set_state(None)
    await msg.delete()


@dp.callback_query_handler(greeting_action.filter(action="delete_greeting"))
async def delete_greeting(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    greeting = greeting_db.get(int(callback_data["id"]))
    callback_data["id"] = greeting.bot
    greeting_db.delete(greeting.id)
    await greeting_list(cb, callback_data, state)


@dp.callback_query_handler(greeting_action.filter(action="greeting_off"))
async def greeting_off(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    greeting = greeting_db.get(int(callback_data["id"]))
    greeting.active = False
    greeting_db.update(greeting)
    await send_greeting_menu_cb(cb, callback_data, state)


@dp.callback_query_handler(greeting_action.filter(action="greeting_on"))
async def greeting_on(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    greeting = greeting_db.get(int(callback_data["id"]))
    greeting.active = True
    greeting_db.update(greeting)
    await send_greeting_menu_cb(cb, callback_data, state)


@dp.callback_query_handler(greeting_action.filter(action="add_greeting_buttons"))
async def add_greeting_buttons(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    msg = await cb.message.answer(
        "Щоб додати кнопки-посилання надішліть список у форматі\nпідпис1 - посилання1\nпідпис2 - посилання2\n...",
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
    greeting = greeting_db.get(state_data["greeting_id"])
    try:
        greeting.buttons = models.deserialize_buttons(msg.text)
    except ValueError:
        await bot.edit_message_text(
            "Невірний формат. Cпробуйте ще раз\nЩоб додати кнопки-посилання надішліть список у форматі\nпідпис1 - посилання1\nпідпис2 - посилання2\n...",
            msg.from_user.id,
            state_data["msg_id"],
            reply_markup=gen_cancel(
                greeting_action.new(
                    id=greeting.id,
                    action="open_greeting_menu"
                )
            )
        )
        return
    greeting_db.update(greeting)
    await state.set_state(None)
    await send_greeting_menu(msg.from_user.id, greeting.id, state_data["msg_id"])


async def greeting_schedule_menu(uid: int, greeting_id: int, msg_id: int):
    greeting = greeting_db.get(greeting_id)
    await bot.send_message(
        uid,
        f"/text5/\n<i>📩Затримка надсилання: {f'{greeting.send_delay} сек.' if greeting.send_delay else 'немає'}\n\
♻️Затримка автовидалення: {f'{greeting.del_delay} сек.' if greeting.del_delay else 'немає'}</i>",
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
        "Введіть затримку надсилання (у секундах)",
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
    if msg.text.isdigit() and int(msg.text) > 0 and int(msg.text) < 86400:
        await state.set_state(None)       
        greeting = greeting_db.get(state_data["greeting_id"])
        greeting.send_delay = int(msg.text)
        greeting_db.update(greeting)
        await msg.delete()
        await greeting_schedule_menu(msg.from_user.id, greeting.id, state_data["msg_id"])
    else:
        await safe_del_msg(msg.from_user.id, msg.message_id)
        try:
            await bot.edit_message_text(
                "❗️Затримка має бути цілим додатнім числом. Від 1 до 86399\nВведіть затримку надсилання (у секундах)",
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
    greeting = greeting_db.get(int(callback_data["id"]))
    greeting.send_delay = None
    greeting_db.update(greeting)
    await greeting_schedule_menu(cb.from_user.id, int(callback_data["id"]), cb.message.message_id)


@dp.callback_query_handler(greeting_action.filter(action="edit_del_delay"))
async def edit_del_delay(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    greeting = greeting_db.get(int(callback_data["id"]))
    bot_dc = bots_db.get(greeting.bot)
    msg = await cb.message.answer(
        "Введіть затримку автовидалення (у секундах)",
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


@dp.message_handler(lambda msg: msg.text.isdigit(), content_types=ContentTypes.TEXT, state=states.InputStateGroup.greeting_del_delay)
async def edit_del_delay(msg: Message, state: FSMContext):
    await state.set_state(None)
    state_data = await state.get_data()
    greeting = greeting_db.get(state_data["greeting_id"])
    greeting.del_delay = int(msg.text)
    greeting_db.update(greeting)
    await msg.delete()
    await greeting_schedule_menu(msg.from_user.id, greeting.id, state_data["msg_id"])


@dp.callback_query_handler(greeting_action.filter(action="del_del_delay"))
async def del_del_delay(cb: CallbackQuery, callback_data: dict):
    greeting = greeting_db.get(int(callback_data["id"]))
    greeting.del_delay = None
    greeting_db.update(greeting)
    await greeting_schedule_menu(cb.from_user.id, int(callback_data["id"]), cb.message.message_id)
