from bot.misc import *

bot_action = CallbackData("bot_action", "id", "action")
greeting_action = CallbackData("greeting_action", "id", "action")
mail_action = CallbackData("mail_action", "id", "action")
captcha_action = CallbackData("captcha_action", "id", "action")
purge_action = CallbackData("purge_action", "id", "action")


def gen_cancel(callback_data: str) -> InlineKeyboardMarkup:
    cancel = InlineKeyboardMarkup()
    cancel.add(
        InlineKeyboardButton(
            "❌Відміна",
            callback_data=callback_data
        )
    )
    return cancel


def gen_confirmation(action_true: str, action_false) -> InlineKeyboardMarkup:
    confirm_bar = InlineKeyboardMarkup()
    confirm_bar.add(
        InlineKeyboardButton(
            "❌ Ні",
            callback_data=action_false
        ),
        InlineKeyboardButton(
            "✅ Taк",
            callback_data=action_true
        )
    )
    return confirm_bar
