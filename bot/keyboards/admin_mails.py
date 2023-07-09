from bot.misc import *
from bot.keyboards import admin_mail_action


def gen_admin_mail_list(admin_mails: list[models.AdminMail]) -> InlineKeyboardMarkup:
    mail_list = InlineKeyboardMarkup()
    for admin_mail in admin_mails:
        mail_list.add(
            InlineKeyboardButton(
                f"{admin_mail.text[:20]}..." if admin_mail.text else gen_hex_caption(admin_mail.id),
                callback_data=admin_mail_action.new(
                    id=admin_mail.id,
                    action="open_admin_mail_menu"
                )
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


def gen_admin_mail_menu(admin_mail: models.AdminMail) -> InlineKeyboardMarkup:
    admin_mail_menu = InlineKeyboardMarkup()
    for button_row in admin_mail.buttons:
        row_buttons = []
        for button_dict in button_row:
            button = InlineKeyboardButton(button_dict["caption"], url=button_dict["link"])
            row_buttons.append(button)
        admin_mail_menu.row(*row_buttons)
    admin_mail_menu.add(
        InlineKeyboardButton(
            "🔥Запустити",
            callback_data=admin_mail_action.new(
                admin_mail.id,
                "sendout"
            )
        ),
        InlineKeyboardButton(
            "➕Додати кнопки",
            callback_data=admin_mail_action.new(
                admin_mail.id,
                "add_buttons"
            )
        )
    )
    admin_mail_menu.add(
        InlineKeyboardButton(
            "↩️Назад",
            callback_data="admin_mails"
        ),
        InlineKeyboardButton(
            "🗑Видалити",
            callback_data=admin_mail_action.new(
                admin_mail.id,
                "delete_admin_mail"
            )
        )
    )
    return admin_mail_menu
