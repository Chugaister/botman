from bot.misc import *
from . import bot_action, gen_cancel, mail_action


def gen_admin_mail_list(admin_mails: list[models.Admin_mail]) -> InlineKeyboardMarkup:
    mail_list = InlineKeyboardMarkup()
    for admin_mail in admin_mails:
        mail_list.add(
            InlineKeyboardButton(
                f"{admin_mail.text[:20]}..." if admin_mail.text else gen_hex_caption(admin_mail.id),
                callback_data="open_admin_mail_menu"
            )
        )
    mail_list.add(
        InlineKeyboardButton(
            "↩️Назад",
            callback_data="admin"
        ),
        InlineKeyboardButton(
            "➕Додати",
            callback_data="add_admin_mail"
            )
    )
    return mail_list
