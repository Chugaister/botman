from bot.misc import *
from . import bot_action, gen_cancel, multi_mail_action


def gen_cancel_schedule_menu(multi_mail: models.MultiMail) -> InlineKeyboardMarkup:
    reply_markup = gen_cancel(
        multi_mail_action.new(
            multi_mail.id,
            "schedule",
            extra_field=0
        )
    )
    return reply_markup


def gen_multi_mail_list(multi_mails: list[models.MultiMail]) -> InlineKeyboardMarkup:
    multi_mail_list = InlineKeyboardMarkup()
    for multi_mail in multi_mails:
        schedule_mark = '🕑' if multi_mail.send_dt or multi_mail.del_dt else ''
        multi_mail_list.add(
            InlineKeyboardButton(
                schedule_mark + (f"{multi_mail.text[:20]}..." if multi_mail.text else gen_hex_caption(multi_mail.id)),
                callback_data=multi_mail_action.new(
                    id=multi_mail.id,
                    action="open_multi_mail_menu",
                    extra_field=0
                )
            )
        )
    multi_mail_list.add(
        InlineKeyboardButton(
            "↩️Назад",
            callback_data="start_msg"
        ),
        InlineKeyboardButton(
            "➕Додати",
            callback_data="add_multi_mail"
        )
    )
    return multi_mail_list


def gen_bot_select_menu(multi_mail: models.MultiMail, bots_dc: list[models.Bot]) -> InlineKeyboardMarkup:
    bot_select_menu = InlineKeyboardMarkup()
    for bot_dc in bots_dc:
        button = InlineKeyboardButton(
            f"✅@{bot_dc.username}",
            callback_data=multi_mail_action.new(
                id=multi_mail.id,
                action=f"detach_bot",
                extra_field=bot_dc.id
            )
        ) if bot_dc.id in multi_mail.bots else InlineKeyboardButton(
            f"☑️@{bot_dc.username}",
            callback_data=multi_mail_action.new(
                id=multi_mail.id,
                action=f"attach_bot",
                extra_field=bot_dc.id
            )
        )
        bot_select_menu.add(
            button
        )
    bot_select_menu.add(
        InlineKeyboardButton(
            "📥Готово",
            callback_data=multi_mail_action.new(
                id=multi_mail.id,
                action="open_multi_mail_menu",
                extra_field=0
            )
        )
    )
    return bot_select_menu


def gen_multi_mail_menu(multi_mail: models.MultiMail) -> InlineKeyboardMarkup:
    mail_menu = InlineKeyboardMarkup()
    for button_row in multi_mail.buttons:
        row_buttons = []
        for button_dict in button_row:
            button = InlineKeyboardButton(button_dict["caption"], url=button_dict["link"])
            row_buttons.append(button)
        mail_menu.row(*row_buttons)
    mail_menu.add(
        InlineKeyboardButton(
            "✏️Редагувати",
            callback_data=multi_mail_action.new(
                multi_mail.id,
                "edit_multi_mail",
                extra_field=0
            )
        ),
        InlineKeyboardButton(
            "➕Додати кнопки",
            callback_data=multi_mail_action.new(
                multi_mail.id,
                "add_buttons",
                extra_field=0
            )
        )
    )
    if multi_mail.admin:
        mail_menu.add(
            InlineKeyboardButton(
                "🔥Запустити",
                callback_data=multi_mail_action.new(
                    multi_mail.id,
                    "sendout",
                    extra_field=0
                )
            ),
            InlineKeyboardButton(
                "🕑Планування",
                callback_data=multi_mail_action.new(
                    multi_mail.id,
                    "schedule",
                    extra_field=0
                )
            )
        )
    else:
        mail_menu.add(
            InlineKeyboardButton(
                "🔥Запустити",
                callback_data=multi_mail_action.new(
                    multi_mail.id,
                    "sendout",
                    extra_field=0
                )
            ),
            InlineKeyboardButton(
                "🕑Планування",
                callback_data=multi_mail_action.new(
                    multi_mail.id,
                    "schedule",
                    extra_field=0
                )
            ),
            InlineKeyboardButton(
                "🤖Боти",
                callback_data=multi_mail_action.new(
                    multi_mail.id,
                    "bots_select",
                    extra_field=0
                )
            )
        )
    mail_menu.add(
        InlineKeyboardButton(
            "↩️Назад",
            callback_data="multi_mails"
        ),
        InlineKeyboardButton(
            "🗑Видалити",
            callback_data=multi_mail_action.new(
                multi_mail.id,
                "delete_mail",
                extra_field=0
            )
        )
    )
    return mail_menu


def gen_schedule_menu(mail: models.Mail) -> InlineKeyboardMarkup:
    schedule_menu = InlineKeyboardMarkup()
    schedule_menu.add(
        InlineKeyboardButton(
            "✏️Надсилання",
            callback_data=multi_mail_action.new(
                mail.id,
                "edit_send_dt",
                extra_field=0
            )
        ),
        InlineKeyboardButton(
            "🗑Надсилання",
            callback_data=multi_mail_action.new(
                mail.id,
                "del_send_dt",
                extra_field=0
            )
        )
    )
    schedule_menu.add(
        InlineKeyboardButton(
            "✏️Автовидалення",
            callback_data=multi_mail_action.new(
                mail.id,
                "edit_del_dt",
                extra_field=0
            )
        ),
        InlineKeyboardButton(
            "🗑Автовидалення",
            callback_data=multi_mail_action.new(
                mail.id,
                "del_del_dt",
                extra_field=0
            )
        )
    )
    schedule_menu.add(
        InlineKeyboardButton(
            "📥Зберегти",
            callback_data=multi_mail_action.new(
                id=mail.id,
                action="open_multi_mail_menu",
                extra_field=0
            )
        )
    )
    return schedule_menu

