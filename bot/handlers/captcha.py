import bot.handlers.settings
from bot.misc import *
from bot.keyboards import captcha as kb
from bot.keyboards import bot_action, captcha_action, gen_cancel


async def open_captcha_menu(uid: int, captcha_id: int, msg_id: int):
    captcha = captchas_db.get(captcha_id)
    bot_dc = bots_db.get(captcha.bot)
    if captcha.photo:
        file = await file_manager.get_file(captcha.photo)
        await bot.send_photo(uid, file, caption=captcha.text, reply_markup=kb.gen_captcha_menu(bot_dc, captcha))
    elif captcha.video:
        file = await file_manager.get_file(captcha.video)
        await bot.send_video(uid, file, caption=captcha.text, reply_markup=kb.gen_captcha_menu(bot_dc, captcha))
    elif captcha.gif:
        file = await file_manager.get_file(captcha.gif)
        await bot.send_animation(uid, file, caption=captcha.text, reply_markup=kb.gen_captcha_menu(bot_dc, captcha))
    else:
        await bot.send_message(uid, captcha.text, reply_markup=kb.gen_captcha_menu(bot_dc, captcha))
    await safe_del_msg(uid, msg_id)


@dp.callback_query_handler(bot_action.filter(action="captcha"), state="*")
async def open_captcha_menu_cb(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.set_state(None)
    captcha = captchas_db.get_by(bot=int(callback_data["id"]))[0]
    await open_captcha_menu(cb.from_user.id, captcha.id, cb.message.message_id)


@dp.callback_query_handler(captcha_action.filter(action="captcha_on"))
async def captcha_on(cb: CallbackQuery, callback_data: dict):
    captcha = captchas_db.get(int(callback_data["id"]))
    captcha.active = True
    captchas_db.update(captcha)
    await open_captcha_menu(cb.from_user.id, captcha.id, cb.message.message_id)


@dp.callback_query_handler(captcha_action.filter(action="captcha_off"))
async def captcha_off(cb: CallbackQuery, callback_data: dict):
    captcha = captchas_db.get(int(callback_data["id"]))
    captcha.active = False
    captchas_db.update(captcha)
    await open_captcha_menu(cb.from_user.id, captcha.id, cb.message.message_id)


@dp.callback_query_handler(captcha_action.filter(action="set_captcha"))
async def set_captcha(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    captcha = captchas_db.get(int(callback_data["id"]))
    msg = await cb.message.answer(
        "Надішліть текст, гіф, фото або відео з підписом",
        reply_markup=gen_cancel(bot_action.new(id=captcha.bot, action="captcha"))
    )
    await state.set_state(states.InputStateGroup.captcha)
    await state.set_data({"captcha_id": int(callback_data["id"]), "msg_id": msg.message_id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.captcha)
async def set_captcha_text(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    await state.set_state(None)
    captcha = captchas_db.get(state_data["captcha_id"])
    captcha.text = msg.text
    captcha.photo = None
    captcha.video = None
    captcha.gif = None
    captchas_db.update(captcha)
    await msg.delete()
    await open_captcha_menu(msg.from_user.id, captcha.id, state_data["msg_id"])


@dp.message_handler(content_types=ContentTypes.PHOTO, state=states.InputStateGroup.captcha)
async def set_captcha_photo(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    await state.set_state(None)
    captcha = captchas_db.get(state_data["captcha_id"])
    captcha.text = msg.caption
    captcha.photo = await file_manager.download_file(bot, captcha.bot, msg.photo[-1].file_id)
    captcha.video = None
    captcha.gif = None
    captchas_db.update(captcha)
    await msg.delete()
    await open_captcha_menu(msg.from_user.id, captcha.id, state_data["msg_id"])


@dp.message_handler(content_types=ContentTypes.VIDEO, state=states.InputStateGroup.captcha)
async def set_captcha_video(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    await state.set_state(None)
    captcha = captchas_db.get(state_data["captcha_id"])
    captcha.text = msg.caption
    captcha.photo = None
    captcha.video = await file_manager.download_file(bot, captcha.bot, msg.video.file_id)
    captcha.gif = None
    captchas_db.update(captcha)
    await msg.delete()
    await open_captcha_menu(msg.from_user.id, captcha.id, state_data["msg_id"])


@dp.message_handler(content_types=ContentTypes.ANIMATION, state=states.InputStateGroup.captcha)
async def set_captcha_gif(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    await state.set_state(None)
    captcha = captchas_db.get(state_data["captcha_id"])
    captcha.text = msg.caption
    captcha.photo = None
    captcha.video = None
    captcha.gif = await file_manager.download_file(bot, captcha.bot, msg.animation.file_id)
    captchas_db.update(captcha)
    await msg.delete()
    await open_captcha_menu(msg.from_user.id, captcha.id, state_data["msg_id"])


@dp.callback_query_handler(captcha_action.filter(action="set_buttons"))
async def set_buttons_entry(cb: CallbackQuery, callback_data: dict, state: FSMContext):
    captcha = captchas_db.get(int(callback_data["id"]))
    msg = await cb.message.answer(
        "Введіть кнопки у форматi\n<i>підпис1\nпідпис2\n...</i>",
        reply_markup=gen_cancel(bot_action.new(id=captcha.bot, action="captcha"))
    )
    await state.set_state(states.InputStateGroup.captcha_buttons)
    await state.set_data({"msg_id": msg.message_id, "captcha_id": captcha.id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.captcha_buttons)
async def set_buttons(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    await state.set_state(None)
    captcha = captchas_db.get(state_data["captcha_id"])
    captcha.buttons = models.deserialize_reply_buttons(msg.text)
    captchas_db.update(captcha)
    await open_captcha_menu(msg.from_user.id, captcha.id, state_data["msg_id"])
    await msg.delete()


@dp.callback_query_handler(lambda cb: cb.data == "reply_buttons_info")
async def reply_button_info(cb: CallbackQuery):
    await cb.answer("Користувачі будуть бачити ці кнопки як реплай-клавіатуру (кнопки знизу над клавіатурою)")
