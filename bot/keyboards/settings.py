from bot.misc import *
from . import *


def gen_settings_menu(bot: models.Bot) -> InlineKeyboardMarkup:
    settings_menu = InlineKeyboardMarkup()
    settings_menu.add(
        InlineKeyboardButton(
            "↩️Назад",
            callback_data=bot_action.new(
                bot.id,
                "open_menu"
            )
        ),
        InlineKeyboardButton(
            "🗑Видалити бота",
            callback_data=bot_action.new(
                bot.id,
                "delete_bot"
            )
        )
    )
    return settings_menu
