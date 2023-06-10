from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup


# def gen_custom_buttons(buttons: list[list[dict]]):
#     custom_buttons = InlineKeyboardMarkup()
#     custom_buttons.add(
#         *[
#             InlineKeyboardButton(
#                 button["caption"],
#                 url=button["link"]
#             ) for button in buttons
#         ]
#     )
#     return custom_buttons

def gen_custom_buttons(buttons: list[list[dict]]):
    custom_buttons = InlineKeyboardMarkup()
    for button_row in buttons:
        row_buttons = []
        for button_dict in button_row:
            button = InlineKeyboardButton(button_dict["caption"], url=button_dict["link"])
            row_buttons.append(button)
        custom_buttons.row(*row_buttons)
    return custom_buttons


def gen_custom_reply_buttons(buttons: list[list[str]]):
    custom_buttons = ReplyKeyboardMarkup(resize_keyboard=True)
    for button_list in buttons:
        custom_buttons.add(*button_list)
    return custom_buttons
