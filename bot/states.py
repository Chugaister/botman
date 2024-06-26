from aiogram.dispatcher.filters.state import State, StatesGroup


class InputStateGroup(StatesGroup):
    token = State()

    greeting = State()
    greeting_buttons = State()
    greeting_send_delay = State()
    greeting_del_delay = State()

    mail = State()
    mail_buttons = State()
    mail_send_dt = State()
    mail_del_dt = State()

    admin_mail = State()
    multi_mail = State()
    multi_mail_buttons = State()
    multi_mail_send_dt = State()
    multi_mail_del_dt = State()

    admin_notification = State()
    admin_notification_send = State()

    captcha = State()
    captcha_buttons = State()
    captcha_del_delay = State()

    purge_sched_dt = State()

    bot_username = State()

