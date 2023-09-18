import bot.handlers.settings
from bot.misc import *
from bot.keyboards import admin_panel as kb
from bot.keyboards import gen_cancel, admin_bot_action, gen_ok
import os
from bot.config import WEBHOOK_HOST, secret_key
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
    await state.set_state(None)
    await cb.message.answer(
        "Адмін-панель",
        reply_markup=kb.admin_panel_menu
    )
    await cb.message.delete()


@dp.message_handler(lambda msg: msg.from_user.id in config.admin_list, commands="admin")
async def send_admin_panel(msg: Message):
    await msg.answer(
        "Адмін-панель",
        reply_markup=kb.admin_panel_menu
    )
    await msg.delete()


@dp.callback_query_handler(lambda cb: cb.data == "bots_admin")
async def set_premium(cb: CallbackQuery, state: FSMContext):
    text = "Боти в системі:\n\n"
    ubot_dc_list = await bots_db.get_all()
    for ubot_dc in ubot_dc_list:
        text += "\t@" + ubot_dc.username + "\n\n"
    text += "Введіть юзернейм бота"
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


@dp.callback_query_handler(lambda cb: cb.data == "admin_mails_list")
async def admin_mail_list(cb: CallbackQuery):
    await cb.answer(
        "👨‍💻In development. Coming soon..."
    )

@dp.callback_query_handler(lambda cb: cb.data == "logs_menu")
async def logs(cb: CallbackQuery):
    await cb.message.answer(
        f'''<code>{display_file_list_as_table(list_files_and_last_modified(log_directory))}</code>\n
        {download_strings(list_files_and_last_modified(log_directory))}'''
    )
