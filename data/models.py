from datetime import datetime

import requests.exceptions
from requests import get


DT_FORMAT = "%H:%M %d.%m.%Y"


# def deserialize_buttons(text: str) -> list[dict]:
#     buttons = []
#     if text is None:
#         return buttons
#     for row in text.split("\n"):
#         caption, link = row.split(" - ")
#         if not "https://" in link:
#             link = "https://" + link
#         try:
#             req = get(link)
#         except requests.exceptions.ConnectionError:
#             raise ValueError
#         if not req.ok:
#             raise ValueError
#         buttons.append({
#             "caption": caption,
#             "link": link
#         })
#     return buttons
def deserialize_buttons(text: str) -> list[list[dict]]:
    buttons = []
    if text is None:
        return buttons
    for row in text.split("\n"):
        button_dicts = []
        for button in row.split(" | "):
            caption, link = button.split(" - ")
            if not link.startswith("https://"):
                link = "https://" + link
            try:
                req = requests.get(link)
            except requests.exceptions.ConnectionError:
                raise ValueError
            if not req.ok:
                raise ValueError
            button_dicts.append({"caption": caption.strip(), "link": link})
        buttons.append(button_dicts)
    return buttons


# def serialize_buttons(buttons: list[dict]) -> str:
#     if buttons == []:
#         return None
#     text = "\n".join([f"{button['caption']} - {button['link']}" for button in buttons])
#     return text
def serialize_buttons(buttons: list[list[dict]]) -> str:
    if not buttons:
        return None
    serialized_rows = []
    for button_row in buttons:
        serialized_buttons = [f"{button['caption']} - {button['link']}" for button in button_row]
        serialized_rows.append(" | ".join(serialized_buttons))
    text = "\n".join(serialized_rows)
    return text


def deserialize_reply_buttons(text: str) -> list[list[str]]:
    reply_buttons = []
    for row in text.split("\n"):
        captions = row.split(" | ")
        reply_buttons.append(captions)
    return reply_buttons

def serialize_reply_buttons(buttons: list[list[str]]) -> str:
    rows = []
    for row in buttons:
        row_text = " | ".join(row)
        rows.append(row_text)
    return "\n".join(rows)


class Admin:

    columns = (
        "id",
        "username",
        "first_name",
        "last_name"
    )

    def __init__(self, _id: int, username: str, first_name: str, last_name: str):
        self.id = _id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name

    def get_tuple(self):
        return self.id, self.username, self.first_name, self.last_name


class Bot:

    columns = (
        "id",
        "token",
        "username",
        "admin",
        "status",
        "premium",
        "settings"
    )

    def __init__(self, _id: int, token: str, username: str, admin: int, status: int = 1, premium: int = 0, settings: int = 0):
        self.id = _id
        self.token = token
        self.username = username
        self.admin = admin
        self.status = status
        self.premium = premium
        self.settings = settings

    def get_tuple(self):
        return self.id, self.token, self.username, self.admin, self.status, self.premium, self.settings


class User:

    columns = (
        "id",
        "bot",
        "username",
        "first_name",
        "last_name",
        "status",
        "join_dt"
    )

    def __init__(self, _id: int, bot: int, username: str, first_name: str, last_name: str, status: bool, join_dt: str):
        self.id = _id
        self.bot = bot
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.status = status
        self.join_dt = datetime.strptime(join_dt, DT_FORMAT)

    def get_tuple(self):
        return self.id, self.bot, self.username, self.first_name, self.last_name, self.status, self.join_dt.strftime(DT_FORMAT)


class Captcha:

    columns = (
        "bot",
        "active",
        "text",
        "photo",
        "video",
        "gif",
        "buttons"
    )

    def __init__(
            self,
            _id: int,
            bot: int,
            active: bool = True,
            text: str = None,
            photo: str = None,
            video: str = None,
            gif: str = None,
            buttons: str = None
    ):
        self.id = _id
        self.bot = bot
        self.active = active
        self.text = text
        self.photo = photo
        self.video = video
        self.gif = gif
        self.buttons = deserialize_reply_buttons(buttons)

    def get_tuple(self):
        return self.bot, self.active, self.text, self.photo, self.video, self.gif, serialize_reply_buttons(self.buttons)


class Greeting:

    columns = (
        "bot",
        "active",
        "text",
        "photo",
        "video",
        "gif",
        "buttons",
        "send_delay",
        "del_delay"
    )

    def __init__(
            self,
            _id: int,
            bot: int,
            active: bool = False,
            text: str = None,
            photo: str = None,
            video: str = None,
            gif: str = None,
            buttons: str = None,
            send_delay: int = None,
            del_delay: int = None
    ):
        self.id = _id
        self.bot = bot
        self.active = active
        self.text = text
        self.photo = photo
        self.video = video
        self.gif = gif
        self.buttons = deserialize_buttons(buttons)
        self.send_delay = send_delay
        self.del_delay = del_delay

    def get_tuple(self):
        return (
            self.bot,
            self.active,
            self.text,
            self.photo,
            self.video,
            self.gif,
            serialize_buttons(self.buttons),
            self.send_delay,
            self.del_delay
        )


class Mail:

    columns = (
            "bot",
            "active",
            "text",
            "photo",
            "video",
            "gif",
            "buttons",
            "send_dt",
            "del_dt",
            "status",
            "sent_num",
            "blocked_num",
            "error_num"
    )

    def __init__(
            self,
            _id: int,
            bot: int,
            active: bool = False,
            text: str = None,
            photo: str = None,
            video: str = None,
            gif: str = None,
            buttons: list[dict[str, str]] = None,
            sched_dt: str = None,
            del_dt: str = None,
            status: bool = False,
            sent_num: int = None,
            blocked_num: int = None,
            error_num: int = None
    ):
        self.id = _id
        self.bot = bot
        self.active = active
        self.text = text
        self.photo = photo
        self.video = video
        self.gif = gif
        self.buttons = deserialize_buttons(buttons)
        self.send_dt = datetime.strptime(sched_dt, DT_FORMAT) if sched_dt else None
        self.del_dt = datetime.strptime(del_dt, DT_FORMAT) if del_dt else None
        self.status = status
        self.sent_num = sent_num
        self.blocked_num = blocked_num
        self.error_num = error_num

    def get_tuple(self):
        return (
            self.bot,
            self.active,
            self.text,
            self.photo,
            self.video,
            self.gif,
            serialize_buttons(self.buttons),
            self.send_dt.strftime(DT_FORMAT) if self.send_dt else None,
            self.del_dt.strftime(DT_FORMAT) if self.del_dt else None,
            self.status,
            self.sent_num,
            self.blocked_num,
            self.error_num
        )


class Purge:

    columns = (
            "bot",
            "active",
            "sched_dt",
            "status",
            "deleted_msgs_num",
            "cleared_chats_num",
            "error_num"
    )

    def __init__(
            self,
            _id: int,
            bot: int,
            active: bool = False,
            sched_dt: str = None,
            status: bool = False,
            deleted_msgs_num: int = None,
            cleared_chats_num: int = None,
            error_num: int = None
    ):
        self.id = _id
        self.bot = bot
        self.active = active
        self.sched_dt = datetime.strptime(sched_dt, DT_FORMAT) if sched_dt else None
        self.status = status
        self.deleted_msgs_num = deleted_msgs_num
        self.cleared_chats_num = cleared_chats_num
        self.error_num = error_num

    def get_tuple(self):
        return (
            self.bot,
            self.active,
            self.sched_dt.strftime(DT_FORMAT) if self.sched_dt else None,
            self.status,
            self.deleted_msgs_num,
            self.cleared_chats_num,
            self.error_num,
        )


class Msg:

    columns = (
        "id",
        "user",
        "bot",
        "del_dt",
    )

    def __init__(self, _id: int, user: int, bot: int, del_dt: str = None):
        self.id = _id
        self.user = user
        self.bot = bot
        self.del_dt = datetime.strptime(del_dt, DT_FORMAT) if del_dt else None

    def get_tuple(self):
        return self.id, self.user, self.bot, self.del_dt.strftime(DT_FORMAT) if self.del_dt else None,


