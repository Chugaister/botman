from aiogram import Bot, Dispatcher
from aiogram.utils.exceptions import MessageCantBeDeleted, BotBlocked
from aiogram.types import Message, CallbackQuery, ChatJoinRequest, ContentTypes, ParseMode
from aiogram.dispatcher.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from asyncio import gather, sleep, create_task
from datetime import datetime
from pytz import timezone


from .keyboards import *
from .utils import gen_dynamic_text
from data.factory import *
from data import exceptions as data_exc


class CaptchaStatesGroup(StatesGroup):
    captcha = State()


async def send_captcha(ubot: Bot, udp: Dispatcher, user: models.User):
    # checking advanced settings
    captcha = captchas_db.get_by(bot=ubot.id)[0]
    if not captcha.active:
        return
    if captcha.text:
        captcha.text = gen_dynamic_text(captcha.text, user)
    try:
        if captcha.photo:
            file = await file_manager.get_file(captcha.photo)
            msg = await ubot.send_photo(user.id, file, caption=captcha.text, reply_markup=gen_custom_reply_buttons(captcha.buttons))
        elif captcha.video:
            file = await file_manager.get_file(captcha.video)
            msg = await ubot.send_video(user.id, file, caption=captcha.text, reply_markup=gen_custom_reply_buttons(captcha.buttons))
        elif captcha.gif:
            file = await file_manager.get_file(captcha.gif)
            msg = await ubot.send_animation(user.id, file, caption=captcha.text, reply_markup=gen_custom_reply_buttons(captcha.buttons))
        elif captcha.text:
            msg = await ubot.send_message(user.id, captcha.text, reply_markup=gen_custom_reply_buttons(captcha.buttons))
    except BotBlocked:
        return
    state = udp.current_state(chat=user.id, user=user.id)
    await state.set_state(CaptchaStatesGroup.captcha)
    await state.set_data({"msg_id": msg.message_id})


async def send_greeting(ubot: Bot, uid: int, greeting: models.Greeting):
    if not greeting.active:
        return
    if greeting.text:
        user = user_db.get(uid)
        greeting.text = gen_dynamic_text(greeting.text, user)
    if greeting.send_delay:
        await sleep(greeting.send_delay)
    try:
        if greeting.photo:
            file = await file_manager.get_file(greeting.photo)
            msg = await ubot.send_photo(
                uid,
                file,
                caption=greeting.text,
                reply_markup=gen_custom_buttons(greeting.buttons)
            )
        elif greeting.video:
            file = await file_manager.get_file(greeting.video)
            msg = await ubot.send_video(
                uid,
                file,
                caption=greeting.text,
                reply_markup=gen_custom_buttons(greeting.buttons)
            )
        elif greeting.gif:
            file = await file_manager.get_file(greeting.gif)
            msg = await ubot.send_animation(
                uid,
                file,
                caption=greeting.text,
                reply_markup=gen_custom_buttons(greeting.buttons)
            )
        elif greeting.text:
            msg = await ubot.send_message(
                uid,
                greeting.text,
                reply_markup=gen_custom_buttons(greeting.buttons)
            )
    except BotBlocked:
        return
    if greeting.del_delay:
        await sleep(greeting.del_delay)
        try:
            await msg.delete()
        except MessageCantBeDeleted:
            pass
    else:
        msg_dc = models.Msg(
            msg.message_id,
            uid,
            ubot.id
        )
        msgs_db.add(msg_dc)


async def send_all_greeting(ubot: Bot, uid: int):
    greetings = greeting_db.get_by(bot=ubot.id)
    await gather(*[send_greeting(ubot, uid, greeting) for greeting in greetings])


# chat_join_request_handler
async def req_handler(ubot: Bot, udp: Dispatcher, request: ChatJoinRequest, state: FSMContext):
    captcha = captchas_db.get_by(bot=ubot.id)[0]
    user = models.User(
        request.from_user.id,
        ubot.id,
        request.from_user.username,
        request.from_user.first_name,
        request.from_user.last_name,
        True,
        datetime.now(tz=timezone('Europe/Kiev')).strftime(models.DT_FORMAT)
    )
    if captcha.active:
        await send_captcha(ubot, udp, user)
    else:
        create_task(send_all_greeting(ubot, request.from_user.id))


# message_handler state=captcha
async def captcha_confirm(ubot: Bot, udp: Dispatcher, msg: Message, state: FSMContext):
    user = models.User(
        msg.from_user.id,
        ubot.id,
        msg.from_user.username,
        msg.from_user.first_name,
        msg.from_user.last_name,
        True,
        datetime.now(tz=timezone('Europe/Kiev')).strftime(models.DT_FORMAT)
    )
    try:
        user_db.add(user)
    except data_exc.RecordAlreadyExists:
        pass
    state_data = await state.get_data()
    await msg.delete()
    await ubot.delete_message(msg.from_user.id, state_data["msg_id"])
    await state.set_state(None)
    await send_all_greeting(ubot, msg.from_user.id)


# message_handler command /start
async def start_handler(ubot: Bot, udp: Dispatcher, msg: Message):
    user = models.User(
        msg.from_user.id,
        ubot.id,
        msg.from_user.username,
        msg.from_user.first_name,
        msg.from_user.last_name,
        True,
        datetime.now(tz=timezone('Europe/Kiev')).strftime(models.DT_FORMAT)
    )
    try:
        user_db.add(user)
    except data_exc.RecordAlreadyExists:
        pass
    create_task(send_all_greeting(ubot, msg.from_user.id))
    await msg.delete()
