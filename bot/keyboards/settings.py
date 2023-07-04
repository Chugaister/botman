from bot.misc import *
from . import *


def gen_settings_menu(bot: models.Bot) -> InlineKeyboardMarkup:
    settings_menu = InlineKeyboardMarkup()
    autoapprove_button = InlineKeyboardButton(
        "✅Автоприйом",
        callback_data=bot_action.new(
            bot.id,
            "autoapprove_off"
        )
    ) if bot.settings.get_autoapprove() else InlineKeyboardButton(
        "☑️Автоприйом",
        callback_data=bot_action.new(
            bot.id,
            "autoapprove_on"
        )
    )
    user_collect_button = InlineKeyboardButton(
        "✅Збір користувачів",
        callback_data=bot_action.new(
            bot.id,
            "users_collect_off"
        )
    ) if bot.settings.get_users_collect() else InlineKeyboardButton(
        "☑️Збір користувачів",
        callback_data=bot_action.new(
            bot.id,
            "users_collect_on"
        )
    )
    settings_menu.add(
        autoapprove_button,
        user_collect_button
    )
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
