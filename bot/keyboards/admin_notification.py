from bot.misc import *
from bot.keyboards import admin_notification_action


def admin_notification_menu():
    menu_keyboard = InlineKeyboardMarkup()
    menu_keyboard.add(InlineKeyboardButton(
        "➕Нове сповіщення",
        callback_data=admin_notification_action.new(
            id=0,
            action="add_notification"
        )
    ),
        InlineKeyboardButton(
            "↩️Назад",
            callback_data="admin"
        )
    )
    return menu_keyboard


def admin_notification_confirm():
    notification_confirm = InlineKeyboardMarkup()
    notification_confirm.add(InlineKeyboardButton(
        "🔥Відправити",
        callback_data=admin_notification_action.new(
            id=0,
            action="send_admin_notification")
    ),
        InlineKeyboardButton(
            "❌Відмінити",
            callback_data=admin_notification_action.new(
                id=0,
                action="admin_notification_menu")
        )
    )
    return notification_confirm
