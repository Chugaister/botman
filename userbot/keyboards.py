from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup


def gen_custom_buttons(buttons: list[dict]):
    custom_buttons = InlineKeyboardMarkup()
    custom_buttons.add(
        *[
            InlineKeyboardButton(
                button["caption"],
                url=button["link"]
            ) for button in buttons
        ]
    )
    return custom_buttons


def gen_custom_reply_buttons(buttons: list[str]):
    custom_buttons = ReplyKeyboardMarkup(resize_keyboard=True)
    custom_buttons.add(*buttons)
    return custom_buttons
