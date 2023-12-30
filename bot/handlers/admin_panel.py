import bot.handlers.settings
from bot.handlers.multi_mails import open_multi_mail_menu, safe_get_multi_mail
from bot.misc import *
from bot.keyboards import admin_panel as kb
from bot.keyboards import gen_cancel, admin_bot_action, gen_ok
import os
# from bot.config import WEBHOOK_HOST, secret_key
from configs import config


WEBHOOK_HOST = config.WEBHOOK_HOST
secret_key = config.secret_key
print(WEBHOOK_HOST, secret_key)

log_directory = "/home/user/botman/logs"
def list_files_and_last_modified(directory_path):
    file_list = []
    
    with os.scandir(directory_path) as entries:
        for entry in entries:
            if entry.is_file():
                last_modified = datetime.fromtimestamp(entry.stat().st_mtime)
                formatted_date = last_modified.strftime('%Y-%m-%d %H:%M:%S')
                
                file_info = {
                    "File": entry.name,
                    "Last Modified": formatted_date
                }
                file_list.append(file_info)

    return file_list

def display_file_list_as_table(file_list):
    if not file_list:
        return "No files found."

    table = PrettyTable()
    table.field_names = ["File", "Last Modified"]

    for file_info in file_list:
        table.add_row([file_info["File"], file_info["Last Modified"]])

    return table

def download_strings(file_list):
    res = ''
    for file_info in file_list:
        index = file_info["File"].split(".")[2] if file_info["File"][-1] != 'g' else 0
        res += f'<a href="{WEBHOOK_HOST}/logs/{secret_key}/{index}">{file_info["File"].strip()}</a>\n'
    return res

@dp.callback_query_handler(lambda cb: cb.from_user.id in config.admin_list and cb.data == "admin", state="*")
async def send_admin_panel(cb: CallbackQuery, state: FSMContext):
    try:
        with open("data/source/user_visits.txt", "r") as f:
            users_num = int(f.read())
    except (FileNotFoundError, IndexError):
        users_num = 0
    me = await dp.bot.get_me()
    await cb.message.answer(
        f"Адмін-панель\nРеферальне посилання: https://t.me/{me.username}?start=newyear\n\
Користувачів приєдналося: {users_num}",
        reply_markup=kb.admin_panel_menu
    )
    await cb.message.delete()


@dp.message_handler(lambda msg: msg.from_user.id in config.admin_list, commands="admin")
async def send_admin_panel(msg: Message):
    try: 
        with open("data/source/user_visits.txt", "r") as f:
            users_num = int(f.read())
    except (FileNotFoundError, IndexError):
        users_num = 0
    me = await dp.bot.get_me()
    await msg.answer(
        f"Адмін-панель\nРекламне посилання: https://t.me/{me.username}?start=newyear\n\
Користувачів приєдналося: {users_num}",
        reply_markup=kb.admin_panel_menu
    )
    await msg.delete()


@dp.callback_query_handler(lambda cb: cb.data == "bots_admin")
async def set_premium(cb: CallbackQuery, state: FSMContext):
    text = "Боти в системі:\n\n"
    ubot_dc_list = await bots_db.get_all()
    for ubot_dc in ubot_dc_list:
        text += "\t@" + ubot_dc.username + "\n"
    text += "\nВведіть юзернейм бота"
    msg = await cb.message.answer(
        text,
        reply_markup=gen_cancel("admin")
    )
    await state.set_state(states.InputStateGroup.bot_username)
    await state.set_data({"msg_id": msg.message_id})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


async def send_adminbot_panel(uid: int, bot_id: int, msg_id: int):
    bot_dc = await bots_db.get(bot_id)
    try:
        admin = await admins_db.get(bot_dc.admin)
    except data_exc.RecordIsMissing:
        admin = models.Admin(0, "видалено", "", "")
    await bot.send_message(
        uid,
        f"🤖 @{bot_dc.username}\n🆔 {bot_dc.id}\n👤@{admin.username}\n👑Преміум {bot_dc.premium}\n",
        reply_markup=kb.gen_admin_bot_menu(bot_dc)
    )
    await safe_del_msg(uid, msg_id)


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.bot_username)
async def bot_username_input(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    bot_username = msg.text.replace("@", "")
    bot_list = await bots_db.get_by(username=bot_username)
    await msg.delete()
    if bot_list == []:
        await msg.answer(
            f"Бота з юзернеймом {msg.text} не знайдено",
            reply_markup=gen_ok("hide")
        )
        return
    bot_dc = bot_list[0]
    await send_adminbot_panel(msg.from_user.id, bot_dc.id, state_data["msg_id"])
    await state.set_state(None)


@dp.callback_query_handler(admin_bot_action.filter(action="ban"))
async def ban_bot(cb: CallbackQuery, callback_data: dict):
    bot_dc = await bots_db.get(int(callback_data["id"]))
    bot_dc.status = -1
    await bots_db.update(bot_dc)
    await send_adminbot_panel(cb.from_user.id, bot_dc.id, cb.message.message_id)


@dp.callback_query_handler(admin_bot_action.filter(action="unban"))
async def unban_bot(cb: CallbackQuery, callback_data: dict):
    bot_dc = await bots_db.get(int(callback_data["id"]))
    bot_dc.status = 1
    await bots_db.update(bot_dc)
    await send_adminbot_panel(cb.from_user.id, bot_dc.id, cb.message.message_id)


@dp.callback_query_handler(admin_bot_action.filter(action="premium_add"))
async def premium_add(cb: CallbackQuery, callback_data: dict):
    bot_dc = await bots_db.get(int(callback_data["id"]))
    bot_dc.premium = 1
    await bots_db.update(bot_dc)
    await send_adminbot_panel(cb.from_user.id, bot_dc.id, cb.message.message_id)


@dp.callback_query_handler(admin_bot_action.filter(action="premium_sub"))
async def premium_sub(cb: CallbackQuery, callback_data: dict):
    bot_dc = await bots_db.get(int(callback_data["id"]))
    bot_dc.premium = 0
    await bots_db.update(bot_dc)
    await send_adminbot_panel(cb.from_user.id, bot_dc.id, cb.message.message_id)


@dp.callback_query_handler(lambda cb: cb.data == "hide", state="*")
async def hide(cb: CallbackQuery):
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.callback_query_handler(lambda cb: cb.data == "admin_mails_list", state="*")
async def admin_mail_list(cb: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    admin_mails = await multi_mails_db.get_by(sender=cb.from_user.id, active=0, status=0, admin=1)
    await cb.message.answer(
        "📮Адмін розсилки",
        reply_markup=kb.gen_admin_mail_list(admin_mails)
    )
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


@dp.callback_query_handler(lambda cb: cb.data == "add_admin_mail")
async def add_admin_mail(cb: CallbackQuery, state: FSMContext):
    msg = await cb.message.answer(
        f"Надішліть текст, гіф, фото або відео з підписом.\nДинамічні змінні:\n\
<b>[any]\n[username]\n[first_name]\n[last_name]</b>",
        reply_markup=gen_cancel(
             "admin_mails_list"
        )
    )
    await state.set_state(states.InputStateGroup.admin_mail)
    await state.set_data({"msg_id": msg.message_id, "edit": None})
    await safe_del_msg(cb.from_user.id, cb.message.message_id)


async def admin_mail_input(
        msg: Message, state: FSMContext, text: str = None, photo: str = None, video: str = None, gif: str = None
):
    state_data = await state.get_data()
    admin_mail = models.MultiMail(
        _id=0,
        sender=msg.from_user.id,
        text=text,
        photo=photo,
        video=video,
        gif=gif,
        admin=True
    )
    bots = await bots_db.get_by(premium=0)
    for bot_dc in bots:
        admin_mail.bots.append(bot_dc.id)
    await multi_mails_db.add(admin_mail)
    await state.set_state(None)
    await msg.delete()
    create_task(open_multi_mail_menu(msg.from_user.id, admin_mail.id, state_data["msg_id"]))


@dp.message_handler(content_types=ContentTypes.TEXT, state=states.InputStateGroup.admin_mail)
async def admin_mail_input_text(msg: Message, state: FSMContext):
    await admin_mail_input(
        msg,
        state,
        text=msg.parse_entities(as_html=True) if msg.text else None
    )


@dp.message_handler(content_types=ContentTypes.PHOTO, state=states.InputStateGroup.admin_mail)
async def admin_mail_input_photo(msg: Message, state: FSMContext):
    filename = await file_manager.download_file(bot, f"admin{msg.from_user.id}", msg.photo[-1].file_id)
    await admin_mail_input(
        msg,
        state,
        text=msg.parse_entities(as_html=True) if msg.caption else None,
        photo=filename
    )


@dp.message_handler(content_types=ContentTypes.VIDEO, state=states.InputStateGroup.admin_mail)
async def admin_mail_input_video(msg: Message, state: FSMContext):
    filename = await file_manager.download_file(bot, f"admin{msg.from_user.id}", msg.video.file_id)
    await admin_mail_input(
        msg,
        state,
        text=msg.parse_entities(as_html=True) if msg.caption else None,
        video=filename
    )


@dp.message_handler(content_types=ContentTypes.ANIMATION, state=states.InputStateGroup.admin_mail)
async def admin_mail_input_gif(msg: Message, state: FSMContext):
    filename = await file_manager.download_file(bot, f"admin{msg.from_user.id}", msg.animation.file_id)
    await admin_mail_input(
        msg,
        state,
        text=msg.parse_entities(as_html=True) if msg.caption else None,
        gif=filename
    )


@dp.callback_query_handler(lambda cb: cb.data == "logs_menu")
async def logs(cb: CallbackQuery):
    await cb.message.answer(
        f'''<code>{display_file_list_as_table(list_files_and_last_modified(log_directory))}</code>\n
        {download_strings(list_files_and_last_modified(log_directory))}'''
    )
