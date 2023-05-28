from bot.misc import *
from . import bot_action


def gen_premium_menu(bot: models.Bot) -> InlineKeyboardMarkup:
    premium_menu = InlineKeyboardMarkup()
    premium_menu.add(
        InlineKeyboardButton(
            "↩️Назад",
            callback_data=bot_action.new(
                id=bot.id,
                action="open_menu"
            )
        ),
        InlineKeyboardButton(
            "Адміністратор",
            url=f"https://t.me/{config.admin_username}"
        )
    )
    return premium_menu
