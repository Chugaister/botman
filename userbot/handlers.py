from aiogram import Bot, Dispatcher
from aiogram.utils.exceptions import MessageCantBeDeleted, BotBlocked, MessageToDeleteNotFound, BadRequest, CantInitiateConversation
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


async def safe_del_msg(ubot: Bot, uid: int, msg_id: int):
    try:
        await ubot.delete_message(
            uid,
            msg_id
        )
    except MessageCantBeDeleted:
        pass
    except MessageToDeleteNotFound:
        pass


class CaptchaStatesGroup(StatesGroup):
    captcha = State()


async def send_captcha(ubot: Bot, udp: Dispatcher, user: models.User, request: ChatJoinRequest):
    # checking advanced settings
    captcha = (await captchas_db.get_by(bot=ubot.id))[0]
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
    except CantInitiateConversation:
        return
    state = udp.current_state(chat=user.id, user=user.id)
    await state.set_state(CaptchaStatesGroup.captcha)
    await state.set_data({"msg_id": msg.message_id, "channel_id": request.chat.id})


async def send_greeting(ubot: Bot, user: models.User, greeting: models.Greeting):
    if not greeting.active:
        return
    if greeting.text:
        greeting.text = gen_dynamic_text(greeting.text, user)
    if greeting.send_delay:
        await sleep(greeting.send_delay)
    try:
        if greeting.photo:
            file = await file_manager.get_file(greeting.photo)
            msg = await ubot.send_photo(
                user.id,
                file,
                caption=greeting.text,
                reply_markup=gen_custom_buttons(greeting.buttons)
            )
        elif greeting.video:
            file = await file_manager.get_file(greeting.video)
            msg = await ubot.send_video(
                user.id,
                file,
                caption=greeting.text,
                reply_markup=gen_custom_buttons(greeting.buttons)
            )
        elif greeting.gif:
            file = await file_manager.get_file(greeting.gif)
            msg = await ubot.send_animation(
                user.id,
                file,
                caption=greeting.text,
                reply_markup=gen_custom_buttons(greeting.buttons)
            )
        elif greeting.text:
            msg = await ubot.send_message(
                user.id,
                greeting.text,
                reply_markup=gen_custom_buttons(greeting.buttons)
            )
    except BotBlocked:
        return
    except CantInitiateConversation:
        return
    if greeting.del_delay:
        await sleep(greeting.del_delay)
        try:
            await safe_del_msg(ubot, msg.chat.id, msg.message_id)
        except MessageCantBeDeleted:
            pass
    else:
        msg_dc = models.Msg(
            msg.message_id,
            user.id,
            ubot.id
        )
        await msgs_db.add(msg_dc)


async def send_all_greeting(ubot: Bot, user: models.User):
    greetings = await greeting_db.get_by(bot=ubot.id)
    await gather(*[send_greeting(ubot, user, greeting) for greeting in greetings])


# chat_join_request_handler
async def req_handler(ubot: Bot, udp: Dispatcher, request: ChatJoinRequest, state: FSMContext):
    bot_dc = await bots_db.get(ubot.id)
    captcha = (await captchas_db.get_by(bot=ubot.id))[0]
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
        await send_captcha(ubot, udp, user, request)
    else:
        create_task(send_all_greeting(ubot, user))


# message_handler state=captcha
async def captcha_confirm(ubot: Bot, udp: Dispatcher, msg: Message, state: FSMContext):
    bot_dc = await bots_db.get(ubot.id)
    captcha = (await captchas_db.get_by(bot=ubot.id))[0]
    user = models.User(
        msg.from_user.id,
        ubot.id,
        msg.from_user.username,
        msg.from_user.first_name,
        msg.from_user.last_name,
        True,
        datetime.now(tz=timezone('Europe/Kiev')).strftime(models.DT_FORMAT)
    )
    if bot_dc.settings.get_users_collect():
        try:
            await user_db.add(user)
        except data_exc.RecordAlreadyExists:
            pass
    state_data = await state.get_data()
    await state.set_state(None)
    if bot_dc.settings.get_autoapprove():
        try:
            await ubot.approve_chat_join_request(
                state_data["channel_id"],
                msg.from_user.id
            )
        except BadRequest:
            pass
    create_task(send_all_greeting(ubot, user))
    if captcha.del_delay:
        await sleep(captcha.del_delay)
    await safe_del_msg(ubot, msg.from_user.id, msg.message_id)
    await safe_del_msg(ubot, msg.from_user.id, state_data["msg_id"])


# message_handler command /start
async def start_handler(ubot: Bot, udp: Dispatcher, msg: Message):
    bot_dc = await bots_db.get(ubot.id)
    user = models.User(
        msg.from_user.id,
        ubot.id,
        msg.from_user.username,
        msg.from_user.first_name,
        msg.from_user.last_name,
        True,
        datetime.now(tz=timezone('Europe/Kiev')).strftime(models.DT_FORMAT)
    )
    if bot_dc.settings.get_users_collect():
        try:
            await user_db.add(user)
        except data_exc.RecordAlreadyExists:
            pass
    create_task(send_all_greeting(ubot, user))
    await safe_del_msg(ubot, msg.from_user.id, msg.message_id)
