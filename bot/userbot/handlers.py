from bot.misc import *
from bot.keyboards import gen_custom_buttons, gen_custom_reply_buttons
from aiogram.dispatcher.filters.state import State, StatesGroup
from asyncio import gather


class CaptchaStatesGroup(StatesGroup):
    captcha = State()


async def send_captcha(ubot: Bot, udp: Dispatcher, uid: int):
    # checking advanced settings
    captcha = captchas_db.get_by(bot=ubot.id)[0]
    if not captcha.active:
        return
    if captcha.photo:
        file = await file_manager.get_file(captcha.photo)
        msg = await ubot.send_photo(uid, file, caption=captcha.text, reply_markup=gen_custom_reply_buttons(captcha.buttons))
    elif captcha.video:
        file = await file_manager.get_file(captcha.video)
        msg = await ubot.send_video(uid, file, caption=captcha.text, reply_markup=gen_custom_reply_buttons(captcha.buttons))
    elif captcha.gif:
        file = await file_manager.get_file(captcha.gif)
        await ubot.send_animation(uid, file, caption=captcha.text, reply_markup=gen_custom_reply_buttons(captcha.buttons))
    elif captcha.text:
        msg = await ubot.send_animation(uid, captcha.text)
    state = udp.current_state(chat=uid, user=uid)
    await state.set_state(CaptchaStatesGroup.captcha)
    await state.set_data({"msg_id": msg.message_id})


async def send_greeting(ubot: Bot, uid: int, greeting: models.Greeting):
    if not greeting.active:
        return
    if greeting.send_delay:
        await sleep(greeting.send_delay)
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
    if greeting.del_delay:
        await sleep(greeting.del_delay)
        try:
            await msg.delete()
        except MessageCantBeDeleted:
            pass


async def send_all_greeting(ubot: Bot, uid: int):
    greetings = greeting_db.get_by(bot=ubot.id)
    await gather(*[send_greeting(ubot, uid, greeting) for greeting in greetings])


# chat_join_request_handler
async def req_handler(ubot: Bot, udp: Dispatcher, request: ChatJoinRequest, state: FSMContext):
    await send_captcha(ubot, udp, request.from_user.id)


# message_handler state=captcha
async def captcha_confirm(ubot: Bot, udp: Dispatcher, msg: Message, state: FSMContext):
    state_data = await state.get_data()
    await msg.delete()
    await ubot.delete_message(msg.from_user.id, state_data["msg_id"])
    await state.set_state(None)
    await send_all_greeting(ubot, msg.from_user.id)


# message_handler command /start
async def start_handler(ubot: Bot, udp: Dispatcher, msg: Message):
    await send_all_greeting(ubot, msg.from_user.id)
