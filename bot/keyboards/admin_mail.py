from bot.misc import *
from . import bot_action, gen_cancel, mail_action


def gen_admin_mail_list() -> InlineKeyboardMarkup:
    mail_list = InlineKeyboardMarkup()
    mail_list.add(
        InlineKeyboardButton(
            "↩️Назад",
            callback_data=bot_action.new(
                id=bot.id,
                action="admin"
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