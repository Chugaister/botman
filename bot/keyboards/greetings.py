from bot.misc import *
from . import bot_action, greeting_action


def gen_greeting_list(bot: models.Bot, greetings: list[models.Greeting]) -> InlineKeyboardMarkup:
    greeting_list = InlineKeyboardMarkup()
    for greeting in greetings:
        greeting_list.add(
            InlineKeyboardButton(
                f"{greeting.text[:20]}..." if greeting.text else gen_hex_caption(greeting.id),
                callback_data=greeting_action.new(
                    id=greeting.id,
                    action="open_greeting_menu"
                )
            )
        )
    greeting_list.add(
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
                action="add_greeting"
            )
        )
    )
    return greeting_list


def gen_greeting_menu(bot: models.Bot, greeting: models.Greeting) -> InlineKeyboardMarkup:
    greeting_menu = InlineKeyboardMarkup()
    for button_row in greeting.buttons:
        row_buttons = []
        for button_dict in button_row:
            button = InlineKeyboardButton(button_dict["caption"], url=button_dict["link"])
            row_buttons.append(button)
        greeting_menu.row(*row_buttons)
    switchButton = InlineKeyboardButton(
        "✅Вимкнути",
        callback_data=greeting_action.new(
            greeting.id,
            "greeting_off"
        )
    ) if greeting.active else InlineKeyboardButton(
        "☑️Увімкнути",
        callback_data=greeting_action.new(
            greeting.id,
            "greeting_on"
        )
    )
    greeting_menu.add(
        InlineKeyboardButton(
            "➕Додати кнопки",
            callback_data=greeting_action.new(
                greeting.id,
                "add_greeting_buttons"
            )
        )
    )
    greeting_menu.add(
        switchButton,
        InlineKeyboardButton(
            "🕑Планування",
            callback_data=greeting_action.new(
                greeting.id,
                "schedule"
            )
        )
    )
    greeting_menu.add(
        InlineKeyboardButton(
            "↩️Назад",
            callback_data=bot_action.new(
                bot.id,
                "greetings"
            )
        ),
        InlineKeyboardButton(
            "🗑Видалити",
            callback_data=greeting_action.new(
                greeting.id,
                "delete_greeting"
            )
        )
    )
    return greeting_menu


def gen_timings_menu(greeting: models.Greeting) -> InlineKeyboardMarkup:
    timings_menu = InlineKeyboardMarkup()
    timings_menu.add(
        InlineKeyboardButton(
            "✏️Надсилання",
            callback_data=greeting_action.new(
                greeting.id,
                "edit_send_delay"
            )
        ),
        InlineKeyboardButton(
            "🗑Надсилання",
            callback_data=greeting_action.new(
                greeting.id,
                "del_send_delay"
            )
        )
    )
    timings_menu.add(
        InlineKeyboardButton(
            "✏️Автовидалення",
            callback_data=greeting_action.new(
                greeting.id,
                "edit_del_delay"
            )
        ),
        InlineKeyboardButton(
            "🗑Автовидалення",
            callback_data=greeting_action.new(
                greeting.id,
                "del_del_delay"
            )
        )
    )
    timings_menu.add(
        InlineKeyboardButton(
            "⬅️Назад",
            callback_data=greeting_action.new(
                greeting.id,
                "open_greeting_menu"
            )
        )
    )
    return timings_menu
