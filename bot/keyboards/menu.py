from bot.misc import *
from . import bot_action

go_to_bot_list = InlineKeyboardMarkup()
go_to_bot_list.add(
    InlineKeyboardButton(
        "🤖Боти",
        callback_data="open_bot_list"
    )
)


def gen_bot_list(bots: list[models.Bot]) -> InlineKeyboardMarkup:
    bot_list = InlineKeyboardMarkup()
    for bot in bots:
        bot_list.add(
            InlineKeyboardButton(
                bot.username,
                callback_data=bot_action.new(
                    id=bot.id,
                    action="open_menu"
                )
            )
        )
    bot_list.add(
        InlineKeyboardButton(
            "↩️Назад",
            callback_data="start_msg"
        ),
        InlineKeyboardButton(
            "➕Додати",
            callback_data="add_bot"
        )
    )
    return bot_list


def gen_bot_menu(bot: models.Bot) -> InlineKeyboardMarkup:
    bot_menu = InlineKeyboardMarkup()
    bot_menu.add(
        InlineKeyboardButton(
            "👋Привітання",
            callback_data=bot_action.new(
                id=bot.id,
                action="greetings"
            )
        ),
        InlineKeyboardButton(
            "📩Розсилки",
            callback_data=bot_action.new(
                id=bot.id,
                action="mails"
            )
        )
    )
    bot_menu.add(
        InlineKeyboardButton(
            "🤖Каптча",
            callback_data=bot_action.new(
                id=bot.id,
                action="captcha"
            )
        ),
        InlineKeyboardButton(
            "♻️Чистки",
            callback_data=bot_action.new(
                id=bot.id,
                action="purges"
            )
        )
    )
    bot_menu.add(
        InlineKeyboardButton(
            "⚙️Налаштування",
            callback_data=bot_action.new(
                id=bot.id,
                action="settings"
            )
        ),
        InlineKeyboardButton(
            "👑Преміум",
            callback_data=bot_action.new(
                id=bot.id,
                action="premium"
            )
        )
    )
    bot_menu.add(
        InlineKeyboardButton(
            "↩️Назад",
            callback_data="open_bot_list"
        ),
        InlineKeyboardButton(
            "🔄Оновити",
            callback_data=bot_action.new(
                id=bot.id,
                action="open_menu"
            )
        )
    )
    return bot_menu
