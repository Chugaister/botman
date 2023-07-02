from bot.misc import *
from . import bot_action, captcha_action


def gen_captcha_menu(bot: models.Bot, captcha: models.Captcha) -> InlineKeyboardMarkup:
    captcha_menu = InlineKeyboardMarkup()
    for button_row in captcha.buttons:
        row_buttons = []
        for caption in button_row:
            button = InlineKeyboardButton(caption, callback_data="reply_buttons_info")
            row_buttons.append(button)
        captcha_menu.row(*row_buttons)
    switch_button = InlineKeyboardButton(
        "❌Вимкнути",
        callback_data=captcha_action.new(captcha.id, "captcha_off")
    ) if captcha.active else InlineKeyboardButton(
        "✅Увімкнути",
        callback_data=captcha_action.new(captcha.id, "captcha_on")
    )
    captcha_menu.add(
        InlineKeyboardButton(
            "✏️Змінити кнопки",
            callback_data=captcha_action.new(captcha.id, "set_buttons")
        ),
        InlineKeyboardButton(
            "✏️Змінити вміст",
            callback_data=captcha_action.new(captcha.id, "set_captcha")
        ),
        InlineKeyboardButton(
            "🕑Планування",
            callback_data=captcha_action.new(captcha.id, "schedule")
        )
    )
    captcha_menu.add(
        InlineKeyboardButton(
            "↩️Назад",
            callback_data=bot_action.new(bot.id, "open_menu")
        ),
        switch_button
    )
    return captcha_menu


def gen_timings_menu(captcha: models.Captcha) -> InlineKeyboardMarkup:
    timings_menu = InlineKeyboardMarkup()
    timings_menu.add(
        InlineKeyboardButton(
            "✏️Автовидалення",
            callback_data=captcha_action.new(
                captcha.id,
                "edit_del_delay"
            )
        ),
        InlineKeyboardButton(
            "🗑Автовидалення",
            callback_data=captcha_action.new(
                captcha.id,
                "del_del_delay"
            )
        )
    )
    timings_menu.add(
        InlineKeyboardButton(
            "⬅️Назад",
            callback_data=bot_action.new(
                captcha.bot,
                "captcha"
            )
        )
    )
    return timings_menu
