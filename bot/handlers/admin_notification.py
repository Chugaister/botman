import bot.handlers.settings
from bot.misc import *
from bot.keyboards import admin_notification as kb
from bot.keyboards import admin_notification_action, gen_cancel, gen_ok
from aiogram.utils.exceptions import BotBlocked
from os import remove
from os.path import join
from data.factory import source as source_folder
from data import DIR

admin_notification_stats = []


@dp.callback_query_handler(admin_notification_action.filter(action="admin_notification_menu"), state="*")
async def admin_notification_menu(cb: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    await cb.message.answer(
        "<i>💡В цьому меню, можна відправити сповіщення адмінам ботів(наприклад про час технічних робіт сервісу).</i>",
        reply_markup=kb.admin_notification_menu()
    )
    await cb.message.delete()


@dp.callback_query_handler(admin_notification_action.filter(action="add_notification"))
async def add_mail(cb: CallbackQuery, state: FSMContext):
    msg = await cb.message.answer(
        "Надішліть текст, гіф, фото або відео з підписом.\nДинамічні змінні:\n<b>[any]\n[username]\n[first_name]\n[last_name]</b>",
        reply_markup=gen_cancel(admin_notification_action.new(
            id=0,
            action="admin_notification_menu"
        )
        )
    )
    await state.set_state(states.InputStateGroup.admin_notification)
    await state.set_data({"msg_id": msg.message_id, "bot_id": msg.bot.id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


async def open_admin_notification_send_menu(uid: int, admin_notification: models.AdminNotification, msg_id: int, state: FSMContext):
    if admin_notification.photo:
        file = await file_manager.get_file(admin_notification.photo)
        await bot.send_photo(
            uid,
            file,
            caption=admin_notification.text,
            reply_markup=kb.admin_notification_confirm()
        )
    elif admin_notification.video:
        file = await file_manager.get_file(admin_notification.video)
        await bot.send_video(
            uid,
            file,
            caption=admin_notification.text,
            reply_markup=kb.admin_notification_confirm()
        )
    elif admin_notification.gif:
        file = await file_manager.get_file(admin_notification.gif)
        await bot.send_animation(
            uid,
            file,
            caption=admin_notification.text,
            reply_markup=kb.admin_notification_confirm()
        )
    elif admin_notification.text:
        await bot.send_message(
            uid,
            admin_notification.text,
            reply_markup=kb.admin_notification_confirm()
        )
    await state.set_state(states.InputStateGroup.admin_notification_send)
    await state.set_data({"notification": admin_notification, "uid": uid})
    await safe_del_msg(uid, msg_id)


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.admin_notification)
async def admin_notification_input_text(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    admin_notification = models.AdminNotification(
        _id=0,
        text=msg.parse_entities(as_html=True) if msg.text else None
    )
    await state.set_state(None)
    await msg.delete()
    await open_admin_notification_send_menu(msg.from_user.id, admin_notification, state_data["msg_id"], state)
    return admin_notification


@dp.message_handler(content_types=ContentTypes.PHOTO, state=states.InputStateGroup.admin_notification)
async def admin_notification_input_photo(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    filename = await file_manager.download_file(bot, state_data["bot_id"], msg.photo[-1].file_id)
    admin_notification = models.AdminNotification(
        _id=0,
        text=msg.parse_entities(as_html=True) if msg.caption else None,
        photo=filename
    )
    await state.set_state(None)
    await msg.delete()
    await open_admin_notification_send_menu(msg.from_user.id, admin_notification, state_data["msg_id"], state)


@dp.message_handler(content_types=ContentTypes.VIDEO, state=states.InputStateGroup.admin_notification)
async def admin_notification_input_video(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    filename = await file_manager.download_file(bot, state_data["bot_id"], msg.video.file_id)
    admin_notification = models.AdminNotification(
        _id=0,
        text=msg.parse_entities(as_html=True) if msg.caption else None,
        video=filename
    )
    await state.set_state(None)
    await msg.delete()
    await open_admin_notification_send_menu(msg.from_user.id, admin_notification, state_data["msg_id"], state)


@dp.message_handler(content_types=ContentTypes.ANIMATION, state=states.InputStateGroup.admin_notification)
async def admin_notification_input_video(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    filename = await file_manager.download_file(bot, state_data["bot_id"], msg.animation.file_id)
    admin_notification = models.AdminNotification(
        _id=0,
        text=msg.parse_entities(as_html=True) if msg.caption else None,
        video=filename
    )
    await state.set_state(None)
    await msg.delete()
    await open_admin_notification_send_menu(msg.from_user.id, admin_notification, state_data["msg_id"], state)


def gen_dynamic_text(text: str, user: models.Admin) -> str:
    any = user.first_name if user.first_name else user.username
    text = text.replace("[username]", str(user.username))
    text = text.replace("[first_name]", str(user.first_name))
    text = text.replace("[last_name]", str(user.last_name))
    text = text.replace("[any]", any)
    return text


async def send_notification(admins: list, notification: models.AdminNotification, uid: int):
    sent_num = 0
    blocked_num = 0
    error_num = 0
    for admin in admins:
        await sleep(0.035)
        if notification.text:
            notification.text = gen_dynamic_text(notification.text, admin)
        try:
            if notification.photo:
                await bot.send_photo(
                    admin.id,
                    await file_manager.get_file(notification.photo),
                    caption=notification.text
                )
            elif notification.video:
                await bot.send_video(
                    admin.id,
                    await file_manager.get_file(notification.video),
                    caption=notification.text
                )
            elif notification.gif:
                await bot.send_animation(
                    admin.id,
                    file_manager.get_file(notification.gif),
                    caption=notification.text
                )
            elif notification.text:
                await bot.send_message(
                    admin.id,
                    notification.text
                )
            sent_num += 1
        except BotBlocked:
            blocked_num += 1
        except Exception:
            error_num += 1
    admin_notification_stats.append({
        "admin_id": uid,
        "sent_num": sent_num,
        "blocked_num": blocked_num,
        "error_num": error_num
    })
    if notification.photo:
        remove(join(DIR, source_folder, "media", notification.photo))
    if notification.video:
        remove(join(DIR, source_folder, "media", notification.video))
    if notification.gif:
        remove(join(DIR, source_folder, "media", notification.gif))


@dp.callback_query_handler(state=states.InputStateGroup.admin_notification_send)
async def sendout(cb: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    admins = await admins_db.get_all()
    for send_admin in admins:
        if send_admin.id == state_data["uid"]:
            admins.remove(send_admin)
    await bot.send_message(
        state_data["uid"],
        "Розпочато сповіщення адмінів ботів",
        reply_markup=gen_ok("admin", "↩️Добро")
    )
    await safe_del_msg(cb.from_user.id, cb.message.message_id)
    create_task(send_notification(admins, state_data["notification"], state_data["uid"]))
    await state.set_state(None)
