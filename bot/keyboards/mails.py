from bot.misc import *
from . import bot_action, gen_cancel, mail_action


def gen_mail_list(bot: models.Bot, mails: list[models.Mail]) -> InlineKeyboardMarkup:
    mail_list = InlineKeyboardMarkup()
    for mail in mails:
        mail_list.add(
            InlineKeyboardButton(
                f"{mail.text[:20]}..." if mail.text else gen_hex_caption(mail.id),
                callback_data=mail_action.new(
                    id=mail.id,
                    action="open_mail_menu"
                )
            )
        )
    mail_list.add(
        InlineKeyboardButton(
            "↩️Назад",
            callback_data=bot_action.new(
                id=bot.id,
                action="open_menu"
            )
        ),
        InlineKeyboardButton(
            "➕Додати",
            callback_data=bot_action.new(
                id=bot.id,
                action="add_mail"
            )
        )
    )
    return mail_list


def gen_mail_menu(bot: models.Bot, mail: models.Mail) -> InlineKeyboardMarkup:
    mail_menu = InlineKeyboardMarkup()
    for button_row in mail.buttons:
        row_buttons = []
        for button_dict in button_row:
            button = InlineKeyboardButton(button_dict["caption"], url=button_dict["link"])
            row_buttons.append(button)
        mail_menu.row(*row_buttons)
    mail_menu.add(
        InlineKeyboardButton(
            "➕Додати кнопки",
            callback_data=mail_action.new(
                mail.id,
                "add_buttons"
            )
        )
    )
    mail_menu.add(
        InlineKeyboardButton(
            "🔥Запустити",
            callback_data=mail_action.new(
                mail.id,
                "sendout"
            )
        ),
        InlineKeyboardButton(
            "🕑Планування",
            callback_data=mail_action.new(
                mail.id,
                "schedule"
            )
        )
    )
    mail_menu.add(
        InlineKeyboardButton(
            "↩️Назад",
            callback_data=bot_action.new(
                bot.id,
                "mails"
            )
        ),
        InlineKeyboardButton(
            "🗑Видалити",
            callback_data=mail_action.new(
                mail.id,
                "delete_mail"
            )
        )
    )
    return mail_menu


def gen_schedule_menu(mail: models.Mail) -> InlineKeyboardMarkup:
    schedule_menu = InlineKeyboardMarkup()
    schedule_menu.add(
        InlineKeyboardButton(
            "✏️Надсилання",
            callback_data=mail_action.new(
                mail.id,
                "edit_send_dt"
            )
        ),
        InlineKeyboardButton(
            "🗑Надсилання",
            callback_data=mail_action.new(
                mail.id,
                "del_send_dt"
            )
        )
    )
    schedule_menu.add(
        InlineKeyboardButton(
            "✏️Автовидалення",
            callback_data=mail_action.new(
                mail.id,
                "edit_del_dt"
            )
        ),
        InlineKeyboardButton(
            "🗑Автовидалення",
            callback_data=mail_action.new(
                mail.id,
                "del_del_dt"
            )
        )
    )
    schedule_menu.add(
        InlineKeyboardButton(
            "⬅️Назад",
            callback_data=mail_action.new(
                id=mail.id,
                action="open_mail_menu"
            )
        )
    )
    return schedule_menu
