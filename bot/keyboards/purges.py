from bot.misc import *

from . import bot_action, purge_action


def gen_purge_list(bot: models.Bot, purges: list[models.Purge]) -> InlineKeyboardMarkup:
    purge_list = InlineKeyboardMarkup()
    for purge in purges:
        purge_list.add(
            InlineKeyboardButton(
                f"{hex(purge.id * 1234)}",
                callback_data=purge_action.new(
                    purge.id,
                    "open_menu"
                )
            )
        )
    purge_list.add(
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
                action="add_purge"
            )
        )
    )
    return purge_list


def gen_purge_menu(purge: models.Purge) -> InlineKeyboardMarkup:
    purge_menu = InlineKeyboardMarkup()
    purge_menu.add(
        InlineKeyboardButton(
            "🔥Запустити",
            callback_data=purge_action.new(
                purge.id,
                "run"
            )
        ),
        InlineKeyboardButton(
            "🕑Запланувати",
            callback_data=purge_action.new(
                purge.id,
                "schedule"
            )
        )
    )
    purge_menu.add(
        InlineKeyboardButton(
            "↩️Назад",
            callback_data=bot_action.new(
                id=purge.bot,
                action="purges"
            )
        ),
        InlineKeyboardButton(
            "🗑Видалити",
            callback_data=purge_action.new(
                id=purge.id,
                action="delete_purge"
            )
        )
    )
    return purge_menu
