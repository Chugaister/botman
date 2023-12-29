from bot.misc import *
from bot.keyboards import admin_bot_action, bot_action, multi_mail_action, admin_notification_action

admin_panel_menu = InlineKeyboardMarkup()
admin_panel_menu.add(
    InlineKeyboardButton(
        "📩Розсилка",
        callback_data="admin_mails_list"
    ),
    InlineKeyboardButton(
        "💬Сповіщення",
        callback_data=admin_notification_action.new(
            id=0,
            action="admin_notification_menu"
        )
    )
)
admin_panel_menu.add(
    InlineKeyboardButton(
        "🔽Приховати",
        callback_data="hide"
    ),
    InlineKeyboardButton(
        "📁Логи",
        callback_data="logs_menu"
    )
)

admin_panel_menu.add(
    InlineKeyboardButton(
        "🤖Боти",
        callback_data="bots_admin"
    )
)


def gen_admin_mail_list(multi_mails: list[models.MultiMail]) -> InlineKeyboardMarkup:
    admin_mail_list = InlineKeyboardMarkup()
    for multi_mail in multi_mails:
        schedule_mark = '🕑' if multi_mail.send_dt or multi_mail.del_dt else ''
        admin_mail_list.add(
            InlineKeyboardButton(
                schedule_mark + (f"{multi_mail.text[:20]}..." if multi_mail.text else gen_hex_caption(multi_mail.id)),
                callback_data=multi_mail_action.new(
                    id=multi_mail.id,
                    action="open_multi_mail_menu",
                    extra_field=0
                )
            )
        )
    admin_mail_list.add(
        InlineKeyboardButton(
            "↩️Назад",
            callback_data="start_msg"
        ),
        InlineKeyboardButton(
            "➕Додати",
            callback_data="add_admin_mail"
        )
    )
    return admin_mail_list


def gen_admin_bot_menu(bot: models.Bot) -> InlineKeyboardMarkup:
    admin_bot_menu = InlineKeyboardMarkup()
    premium_button = InlineKeyboardButton(
        "✅Преміум",
        callback_data=admin_bot_action.new(
            bot.id,
            "premium_sub"
        )
    ) if bot.premium > 0 else InlineKeyboardButton(
        "☑️Преміум",
        callback_data=admin_bot_action.new(
            bot.id,
            "premium_add"
        )
    )
    ban_button = InlineKeyboardButton(
        "❌Бан",
        callback_data=admin_bot_action.new(
            bot.id,
            "unban"
        )
    ) if bot.status == -1 else InlineKeyboardButton(
        "✖️Бан",
        callback_data=admin_bot_action.new(
            bot.id,
            "ban"
        )
    )
    admin_bot_menu.add(
        premium_button,
        ban_button
    )
    admin_bot_menu.add(
        InlineKeyboardButton(
            "↩️Назад",
            callback_data="admin"
        ),
        InlineKeyboardButton(
            "📊Управління",
            callback_data=bot_action.new(
                bot.id,
                "open_menu"
            )
        )
    )
    return admin_bot_menu
