from bot.misc import *
from . import bot_action, captcha_action


def gen_captcha_menu(bot: models.Bot, captcha: models.Captcha) -> InlineKeyboardMarkup:
    captcha_menu = InlineKeyboardMarkup()
    reply_buttons = [InlineKeyboardButton(caption, callback_data="reply_buttons_info") for caption in captcha.buttons]
    captcha_menu.add(*reply_buttons)
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
